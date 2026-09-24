# Executable workflow controller (first increment)

Implemented on `v2`, 2026-09-23. This is an optional, dependency-free Python 3.9+
control layer. All existing `skills/` files and installed Codex skills are unchanged.
No installer or plugin registration is required: run from the repository root.

```sh
python3 -B -m unittest discover -s tests -v
python3 -B -m biostat_workflow.demo --scenario revision
python3 -B -m biostat_workflow.demo --scenario success
python3 -B -m biostat_workflow.demo --scenario fatal
python3 -B -m biostat_workflow.demo --scenario stalled
```

The demo uses synthetic handoff results, including a missing-confounder requirement.
It does not load patient data, fit a model, invoke an LLM, or demonstrate clinical
validity. The default example is a causal 30-day risk difference: preparation →
missing-data policy → identification → estimation → review. The first review finds
a time-zero problem, sends the run back to preparation, and forces dependent work
and review to repeat before reporting. The other scenarios demonstrate direct
success, fatal-flaw escalation, and bounded lack of progress.

## Separation of responsibilities

| Layer | Responsibility |
|---|---|
| Existing `skills/biostatistics/SKILL.md` | Human-readable lifecycle and sequencing policy |
| Existing specialist skills and their references | Statistical methods, evidence requirements, diagnostics, reporting guidance |
| `biostat_workflow/controller.py` | Typed state, prerequisite routing, result validation, invalidation, stop policies, serial execution loop |
| Host-supplied `execute(route, state)` | Read the selected skill, perform the work, assess evidence, return a structured `Result` |
| `biostat_workflow/demo.py` | Scripted results to exercise controller behavior without external dependencies |

The controller encodes only sequencing and handoff decisions. It does not copy the
DAG criteria, imputation recipes, modeling diagnostics, evaluation rubric, or
reporting requirements into Python. `Route.skill_path(repo_root)` resolves the
existing domain-policy file. A production host must read that file and relevant
references. Independent-context statistical review, as required by the evaluation
skill, is the host's responsibility; this controller does not spawn reviewers.

Previously the host had to interpret the SKILL.md graph and remember every gate,
revision, and stopping rule in its conversation. Those instructions remain usable
on their own. Hosts opting into this controller now receive deterministic routes,
validated handoffs, bounded calls, immutable transition records, and explicit stop
reasons. Running the controller is necessary to obtain these guarantees: merely
installing the skills does not activate it. The controller cannot establish that an
adapter's claim of statistical readiness is true.

Python dataclasses, enums, and a synchronous loop are sufficient for this graph.
There is no existing graph-runtime dependency in the repository. LangGraph would
add installation and orchestration machinery without improving these deterministic
gates. Reconsider a framework if durable execution, concurrent branches, or hosted
interrupt/resume becomes an actual requirement.

## State and routing contract

`WorkflowState` is immutable and carries:

- `goal`: descriptive, inferential, causal, predictive, or forecasting.
- `stage`: current lifecycle stage; a stopped run retains its next/present stage
  for inspection, while success uses `done`.
- `estimand_ready`, `data_ready`, `identification_ready`: prerequisite evidence.
  For prediction, estimand readiness means a defined prediction target/metric.
- `missing_data_required`, `missing_data_ready`: assessed need and accepted plan.
- `analysis_ready`, `evaluation`, `report_ready`: downstream completion/readiness.
- `revision_count`, `no_progress_count`, `iteration_count`, `stop_reason`, and
  `fatal_flaw` (the explanation requiring human review).

Unknown or mixed goals must be clarified by the host before constructing state;
they are deliberately not silently mapped to an analysis branch. Goal enums must
be explicitly constructed from external strings. Initial readiness flags are
trusted host assertions, intended to support entry with existing reviewed work.
Do not deserialize untrusted claims directly into state. `stage` alone cannot
skip a prerequisite: `route()` derives the next gate from readiness and `settle()`
normalizes the stored stage. Goal changes require a new state and evidence review.

Routing checks gates in this order:

1. Undefined target → `study-design-and-power`.
2. Unprepared data → `data-understanding-preprocessing` (including eligibility,
   time zero and leakage-safe splits, as specified in that skill).
3. Unresolved non-trivial missingness → `missing-data`.
4. Causal goal without identification → `causal-inference`.
5. Uncompleted analysis → `predictive-modeling` for prediction/forecasting;
   `statistical-analysis` for causal, inferential, or descriptive goals.
6. Anything other than a ready review → `method-evaluation`.
7. Ready review without report → `reporting-and-reproducibility`.
8. All applicable gates satisfied → success.

For this conservative first version, all causal goals go through identification,
including trial analyses; the specialist determines the applicable strategy.
Forecasting follows the predictive branch and uses the existing temporal-validation
and forecasting-review references. There is no forecasting model implementation.
Missing-data completion accepts a plan; predictive imputation must still occur
inside resampling, as the domain policy requires.

## Results, revisions, and evidence

`Result` requires a nonempty evidence reference or explanation and one outcome:

- `complete`: the current skill's gate was met. Preparation must explicitly set
  `missing_data_required` to true or false. Review must explicitly return `ready`.
- `blocked`: no gate was met; retry the same route within the stop limits.
- `revise`: identify a current/upstream owner (design, preparation, missing data,
  causal identification, or analysis); invalidate its dependent evidence.
- `fatal`: stop and return the evidence/explanation for human escalation.

Review status names align with the existing evaluation report schema:
`ready`, `conditionally_ready`, `needs_revision`, `not_ready`, and
`insufficient_information` (plus controller-internal `pending`). Only `ready` can
complete review. All other report ratings require a revision target; even
conditional readiness cannot bypass the gate. A host must resolve conditions and
obtain a new ready review. This is a small handoff envelope, **not** a replacement
for or a parser/validator of the complete evaluation report JSON schema. A future
adapter must validate that report and map its findings, including genuinely fatal
flaws, to this envelope; critical severity alone is not automatically fatal.

A revision increments `revision_count` and invalidates analysis, review, and report.
Revising design also clears the target, preparation, missing-data plan, and
identification. Revising preparation clears its data contract, missing-data plan,
and identification. Revising missing data activates that requirement and clears
its plan and identification. Revising identification clears identification.
Revising analysis preserves valid upstream evidence. Noncausal runs cannot request
causal identification, and revisions cannot jump forward past the current stage.
Late missingness findings can send analysis, review, or reporting back to missing
data. Retained review ratings describe the last critique; they cannot authorize
reporting after upstream readiness has been invalidated.

Each `Transition` retains the before-state, selected route and routing reason,
structured result/evidence, and after-state. `run()` returns the final state and
an immutable tuple of these records. No persistence or artifact store is implied.

## Termination semantics

`settle()` is evaluated before dispatch and after accepted results. A previously
stopped state is absorbing: it is never dispatched or silently restarted.
Priority for a newly stopped state is:

| Priority | Condition | Stop reason |
|---|---|---|
| 1 | Fatal flaw reported | `fatal_flaw_human_escalation` |
| 2 | All applicable gates, ready review, and report completed | `success_ready` |
| 3 | Revision requests exceed the allowed repair cycles | `max_revisions` |
| 4 | Consecutive results without gate completion reach threshold | `no_progress_threshold` |
| 5 | Accepted specialist results reach call cap | `max_iterations` |
| 6 | Optional pre-call budget hook returns false | `budget_exhausted` |

Defaults: 3 permitted repair cycles, 3 consecutive non-progress results, 30 calls.
`max_revisions=N` permits execution of N requested repairs; request N+1 is recorded
but its repair is not dispatched. Zero allows the initial analysis but no repairs.
Iteration and no-progress caps stop at equality. Completing the report on the last
allowed call is success. Fatal flaws take precedence over every other new stop.

A blocked result or revision request increments no-progress count. Completing a
required gate resets it. This measures workflow progress, not metric improvement
or novelty of prose. Hosts must return blocked when new evidence does not satisfy
a gate. Repeated repair-and-review oscillation may reset no-progress count but is
still bounded by revision and iteration caps.

The optional `budget(state) -> bool` hook runs before each specialist call; true
means another call is affordable. The host owns time/token/cost accounting and
reservation. Budget exhaustion never grants readiness. It cannot interrupt an
in-flight call: hard timeouts and cancellation are future adapter work. Similarly,
executor/hook exceptions propagate and are not mislabeled success or statistical
fatal flaws. `advance()` supports manual one-step orchestration; callers must use
`settle(..., budget=...)` before dispatch to enforce a budget outside `run()`.

Human escalation means a returned stop reason and explanation. No person is
contacted automatically. All nonsuccess stop reasons need host/user disposition;
the runner does not discard them or continue in the background.

## Validation and remaining work

The standard-library unit suite exercises every goal branch, prerequisite gates,
missingness, trusted mid-lifecycle entry, review ratings, revision invalidation,
late findings, invalid handoffs, every stop condition, exact cap boundaries,
terminal absorption, budget dispatch limits, and exception propagation. It tests
control flow, not the quality of an LLM's statistical judgment.

The roadmap's broader workflow milestone remains partial: durable versioned run
records, run IDs, input fingerprints, artifact provenance, checkpoint/restart
without repeated external side effects, and asynchronous execution are deferred.
This change also does not implement the roadmap's model-based evaluation harness.

- **Memory:** a subsequent opt-in increment now implements project-scoped confirmed
  records, provenance, stage retrieval, corrections/deletion, conflicts, and
  input/dependency invalidation. See [MEMORY.md](MEMORY.md). Automatic host integration
  and real-model quality/cost evaluation remain pending.
- **MCP:** a concrete tool use case, authentication/data boundaries, validated
  adapters, timeouts, bounded retries, failure records, and mock integration tests.
- **Jev / optional decision routing:** Jev means TypeSafe AI’s structured decision
  model. Integration is deferred pending a measured benefit; see [ROADMAP.md](ROADMAP.md).
  The current router selects specialist skills using deterministic prerequisites,
  not models or reasoning budgets. Laya is outside the current scope.
- **Integration:** implement a real host executor and report-schema adapter,
  preserve independent review, and validate deployment separately. Keep installed
  skills untouched until an explicitly scoped installation test is requested.

## Reviewed handoff checkpoints

The optional [reviewed handoff adapter](REVIEWED_HANDOFF.md) now persists versioned states and accepted-result events alongside confirmed memory. It applies this controller unchanged after separate host review. Source integrity and memory-dependency checks guard dispatch; this is not checkpoint/replay of external tool side effects.
