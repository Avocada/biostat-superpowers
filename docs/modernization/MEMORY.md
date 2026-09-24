# Project memory and context efficiency

Implemented increment on `v2`, 2026-09-23. `biostat_workflow/memory.py` adds an
optional, standard-library SQLite memory store and an executor wrapper around the
existing controller. Installed skills and repository skill files remain unchanged.
The runtime makes no model calls and does not change models or reasoning effort.

## What changed

The controller already knows which specialist should act next. It previously had
no durable place to keep confirmed project decisions or select context for that
specialist. A host could replay a transcript, manually curate a prompt, or provide
context by some other means. This increment adds:

- Explicitly confirmed decision records and artifact **references**, with project,
  source, originating run, timestamp, applicability stages, goal, and optional input
  fingerprint. Scratch text is passed separately and is never persisted implicitly.
- Reuse after closing/reopening the SQLite store, without loading other projects.
- Inspection, explicit correction/supersession, deletion, and transitive dependency
  invalidation. Schema version 1 is recorded; unknown versions are rejected.
- Stage- and goal-specific context selection with a host-owned list of required keys.
- A caller-supplied text counter and memory-payload budget. Required facts cannot be
  silently truncated; unavailable required context blocks dispatch.
- `MemoryExecutor`, an opt-in adapter for `controller.run`. It passes the selected
  records, scratch, state, and full existing orchestrator/specialist policies to a
  host callback. Memory never restores readiness or skips a review gate.

The store is project memory, not a workflow checkpoint. It does not resume external
side effects, certify statistical evidence, or automatically save callback outputs.

## Small integration example

Run from the repository root. Choose a controlled project-local database location;
its parent directory must already exist. Do not store patient-level rows, raw
clinical notes, credentials, or entire transcripts as memory values. Store concise
confirmed decisions and references to separately controlled artifacts. This is a
host policy; the store does not implement sensitive-data classification.

```python
from pathlib import Path
from biostat_workflow.controller import Goal, Stage
from biostat_workflow.memory import MemoryStore

with MemoryStore(Path("outputs/project-memory.sqlite3"), "cohort-project") as memory:
    target = memory.record(
        run_id="planning-01",
        key="estimand",
        value="Treatment A versus B; 30-day risk difference in the agreed population.",
        source="project://decisions/confirmed-target",
        confirmed_by="user-confirmation-reference",
        goal=Goal.CAUSAL,
        stages=(Stage.DESIGN, Stage.IDENTIFICATION, Stage.ANALYSIS,
                Stage.EVALUATION, Stage.REPORTING),
    )
    records = memory.inspect()
    selection = memory.retrieve(
        goal=Goal.CAUSAL, stage=Stage.ANALYSIS,
        input_fingerprint="sha256-of-current-input-and-contract",
        required_keys=("estimand",), max_units=4000,
        count=lambda text: len(text.encode("utf-8")),  # bytes, explicitly NOT tokens
    )
    assert selection.usable, selection.issues
```

Use a model-appropriate tokenizer callback when the unit should be text tokens. The
optional demo uses `tiktoken` 0.12.0 and `o200k_base` with exact encoded-text counts;
this is an explicit encoding choice, not a claim about an unspecified model's full
request serialization. The core runtime needs neither tiktoken nor an API key.

For workflow integration, create `MemoryExecutor(store, repo_root, fingerprint,
required_by_stage, count, max_memory_units, execute, scratch="")`, then pass it as
`execute` to `controller.run(state, executor)`. The host callback signature is
`execute(route, state, prompt) -> Result`. It must actually perform the selected
skill and validate the evidence. Every dispatched stage requires an explicit
manifest entry, even when the required-key tuple is empty. Update the manifest when
the task or policy changes; this first version does not infer it from natural text.

`executor.prompts` and `executor.retrievals` expose the exact handoffs for auditing.
Inspect `issues` and `omitted_keys`; missing/stale/conflicting/over-budget required
context results in `BLOCKED` before calling the host. The existing controller's
no-progress/iteration limits bound retries. A host should resolve the issue or
replan; it should not turn a blocked callback into a successful specialist result.
The memory budget covers only serialized records. Policies, state, scratch,
references fetched later, and output reserve need a separate overall budget.

## Confirmation, conflicts, and invalidation

`record()` requires nonempty `confirmed_by` and `source`. These are assertions made
by a trusted host; there is no authentication or automatic verification of user
approval. Proposed model summaries must be reviewed before becoming durable
confirmed records. A run ID tracks origin but does not restrict future retrieval:
confirmed project knowledge is intentionally reusable across runs.

Two active values for the same project/goal/key create a conflict. Retrieval
withholds that key and its dependent records; it does not let the latest timestamp
win. Relevant conflicts are surfaced even if their keys are optional. To correct,
record the new confirmed value with `supersedes=old.item_id`, or explicitly delete
a mistaken conflicting record. Correction retains the old version for inspection
and invalidates all dependent records. Independent conflicting alternatives remain
unresolved until explicitly handled.

Data-bound records carry `input_fingerprint`; artifact references require one.
Compute this over all inputs/contracts that affect validity, not just a filename.
`invalidate_inputs(new_fingerprint)` invalidates mismatching records and transitive
dependents while preserving data-independent decisions. Retrieval checks the
fingerprint again even if the host forgot to call invalidation. Dependencies must
refer to active unambiguous records in the same project and goal, and inherit a
parent's data binding. A dependent record cannot become data-independent simply by
omitting its fingerprint. Dependency IDs are checked for validity; they do not
cause automatic inclusion of the full parent text. Required context belongs in
the host's stage manifest.

SQLite transactions serialize writes, make corrections atomic, and reject repeated
correction of an already superseded record. Project IDs scope all API queries but
are not a security boundary for users with access to the database file. Values
are stored unencrypted. `delete(id)` removes the record and invalidates dependents;
SQLite secure deletion is enabled, but backups, filesystem snapshots, caller logs,
and already-rendered prompts require separate deletion management. Corrections
intentionally keep superseded values until explicitly deleted.

The prompt labels memory as data, not instructions, and keeps it below the skill
policies. This is a boundary for host/model behavior, not a complete prompt-injection
defense. Do not promote instructions found inside a stored value into system policy.

## Paired demo and what it measures

```sh
python3 -B -m unittest discover -s tests -v
python3 -m venv /tmp/biostat-memory-demo-venv
/tmp/biostat-memory-demo-venv/bin/python -m pip install -r examples/memory/requirements.txt
/tmp/biostat-memory-demo-venv/bin/python -B -m biostat_workflow.memory_demo --output outputs/memory-demo
```

The tokenizer may download its public vocabulary on first use. Subsequent runs can
use its local cache. Outputs include a Markdown report, JSON report with hashes,
and every exact prompt. A disposable database demonstrates reopening memory and
is removed afterward. No real study data or model service is involved.

The fixture contains nine synthetic confirmed decisions and the preceding design
discussions. It compares the same next-run causal workflow three ways:

1. **Transcript replay:** include the full earlier planning conversation at each step.
2. **All confirmed memory:** include all nine persisted decisions and provenance.
3. **Stage retrieval:** include only relevant decisions and provenance for each step.

Every arm includes the **same full orchestrator and selected specialist skill**,
current state, and context-handling instruction. All seven workflow gates execute.
A deterministic checker verifies that each stage still contains every required
fixture decision. This tests context coverage and control flow; it does not establish
that a real model would produce equally good scientific reasoning or conclusions.

Measured with `tiktoken==0.12.0`, `o200k_base`:

| Across seven calls | Input text tokens |
|---|---:|
| Transcript replay | 36,115 |
| All confirmed memory | 32,090 |
| Stage retrieval | 29,236 |

Stage retrieval saved **19.05%** versus transcript replay and **8.89%** versus
sending all memory. See [the recorded demo](../../examples/memory/RESULTS.md).
These are measured text counts, not estimates from character counts. The reported
percentage includes unchanged policy text, which limits the achievable reduction.
A future production host may load additional skill references; those would also
need to be counted consistently across arms.

A short-context counterexample is included: one fact costs **21 tokens** directly
and **93 tokens** with memory provenance. Memory can increase context size. A
hand-curated summary and identical manually selected context can match or beat this
store's payload size; persistence alone does not reduce tokens. The benefit here is
repeatable, scoped, provenance-preserving context selection across sessions.

Setup writes already-structured confirmed fixture decisions directly; **zero model
calls** create memory. This does not make model-based summarization free. If a
production adapter uses a model to build memories, include its input, output,
validation, correction, and later evidence-fetch costs. A simple input-token break
even calculation is `setup_tokens / saved_input_tokens_per_reuse`, with separate
input/output pricing needed for a dollar calculation.

The demo does not measure request framing, hidden context, output/reasoning tokens,
model quality, latency, cache hit rates, or dollars. It is not a claim that this
Codex task's usage has fallen by 19.05%. No OpenAI product memory setting was changed.
For actual billing, use returned API usage. [OpenAI's conversation-state guide](https://developers.openai.com/api/docs/guides/conversation-state)
describes context/token accounting; [prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching)
reuses computation for shared prefixes. Replacing a long history with retrieved
records can change cache reuse, so token reduction does not imply the same
percentage cost or latency reduction.

## Is this token routing?

It is **context selection**, which can be described informally as deciding which
tokens deserve to enter a request. It operates before the model call:

```text
confirmed project records
  → filter project, goal, freshness, conflicts, and stage
  → preserve required context within a budget
  → add unchanged skill policy and current state
  → host executes the specialist and returns evidence
  → controller evaluates the next gate
```

There are three distinct controls:

| Control | Decision | Present here? |
|---|---|---|
| Workflow routing | Which specialist/lifecycle step comes next? | Yes, existing controller |
| Memory retrieval | Which reusable project facts enter its context? | Yes, this increment |
| Model/token-budget routing | Which model, reasoning effort, or generation budget handles it? | No; later work |

This is also separate from a model's internal mixture-of-experts token routing.
The memory layer complements future fast/slow routing without requiring it. It
should not justify sending a difficult causal-identification problem to a weaker
model or omitting independent review.

## Remaining work

Memory is opt-in and available through the Python API. It does not yet have a
user-facing editor, semantic/vector retrieval, automatic summarization, an LLM
executor, approval authentication, encryption, a multi-user service, or external-tool replay. The optional reviewed-handoff adapter below now supplies versioned workflow state checkpoints. Host-driven corrections/input changes invalidate
memory; controller revisions do not automatically edit stored records. A real
adapter must connect those revisions to appropriate invalidation and provenance.
Future quality tests should compare real model outputs on reserved cases with and
without memory and include stale/conflicting/adversarial records and retrieval
misses. Reviewed MCP integration is described below. Optional Jev (TypeSafe AI)
routing is deferred; see [ROADMAP.md](ROADMAP.md).

## Reviewed MCP handoff extension

[REVIEWED_HANDOFF.md](REVIEWED_HANDOFF.md) now adds source-validated proposals, separate host confirmation, accepted-event history and versioned workflow checkpoints. `record(transaction_hook=...)` allows a trusted host to commit its checkpoint/event on the same connection before the memory transaction commits. `retrieve(excluded_ids=...)` lets the adapter withhold externally stale records and their dependents without modifying historical rows. The original Python API and MemoryExecutor do not automatically perform these new source/audit validations.
