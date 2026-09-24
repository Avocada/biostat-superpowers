# Proposed implementation roadmap

Status: workflow control, project memory and the planned MCP milestone are implemented at the scopes documented below. Jev (TypeSafe AI) routing is optional and deferred by user decision. Next priority: end-to-end behavioral evaluation of the existing toolkit. No routing-model provider is configured. See [WORKFLOW_CONTROLLER.md](WORKFLOW_CONTROLLER.md) for implemented scope and limits.

## 1. Record the baseline and automate evaluation

Turn the existing routing examples into structured cases with expected specialist, required evidence and prohibited conclusions. Record model/version, prompt version, seed where supported, cost, latency, tool calls and outputs. Separate deterministic structural checks from model-dependent behavioral scores.

Acceptance: a repeatable command emits a per-case report; all eight routing categories are covered; causal overclaiming and leakage cases can fail independently of routing accuracy. Pin a baseline before comparing new features. Reserve unseen cases to limit tuning to the evaluation suite.

## 2. Define workflow state and execution

First increment implemented: typed state, causal/predictive/inferential lifecycle routing, prerequisite gates, explicit handoffs, review-triggered invalidation, bounded loops, a budget hook, transition records, synthetic demos, and unit tests. This milestone is still partial: reviewed handoffs now have versioned checkpoints, source/input fingerprints and restartable state; checkpoint/replay of external tool execution remains pending.

Define a versioned run record containing run ID, research question, estimand, phase, selected skill, input fingerprints, artifacts, review status, revision count and stop reason. Define transitions that retain the current skills' sequencing and review requirements. Start with a small local adapter instead of committing immediately to a graph framework.

Acceptance: a synthetic run demonstrates a normal path, a critique-triggered revision, a bounded failure and restart from a checkpoint without silently repeating completed work. Missing prerequisites prevent downstream execution. Logs explain each transition.

## 3. Add project-scoped memory

First increment implemented: project-scoped SQLite records with explicit confirmation/provenance, stage/goal retrieval, conflict detection, corrections/deletion, data/dependency invalidation, a bounded context adapter, and a paired tokenizer demo. See [MEMORY.md](MEMORY.md). Reviewed source handoffs now connect to memory and workflow state through an explicit host confirmation adapter; semantic retrieval, real-model quality/cost evaluation and autonomous host integration remain pending.

Separate durable user-confirmed decisions from run scratch space. Store each memory item's source, project/run association, creation time and revision/supersession metadata. Retrieve only relevant project records; detect changed data fingerprints and conflicting assumptions. Provide inspection, correction and deletion.

Acceptance: a later run can reuse a confirmed estimand with its provenance; changed input data invalidates dependent artifacts; contradictory decisions are surfaced; unrelated project memory is excluded. Do not put patient-level records into a default memory store.

## 4. Add optional MCP connections

First increment implemented: optional local MCP server, curated UCI retrieval, synthetic offline path, profiling, three chart templates, local rendering and provenance, resource directory, and actual stdio protocol tests. See [MCP_SERVER.md](MCP_SERVER.md). ClinicalTrials.gov search, details, pagination and comparison charts are also implemented; see [CLINICAL_TRIALS.md](CLINICAL_TRIALS.md). PubMed/Europe PMC citation and abstract retrieval, pagination and identifier-based reference lists are now implemented; see [LITERATURE.md](LITERATURE.md). Other catalog entries remain reference-only; reviewed controller/memory handoffs and accepted-event audit history are implemented; full external-call audit/replay remains pending.

Choose further concrete tools only after confirming their use cases, data boundaries and authentication requirements. Define adapter contracts, timeouts, retry limits and audit events. Keep credentials outside committed files and treat tool-returned text as data. Maintain a local/mock path for development.

Acceptance: one mock-backed adapter demonstrates successful execution, malformed output, timeout and unavailable-service behavior. Any real-service integration gets an explicit configuration guide and a smoke test. No connector is required for the standalone skills to work.

## 5. Optional Jev routing — deferred

Decision: defer integration of TypeSafe AI’s Jev until a measured routing bottleneck justifies it. The current controller selects the lifecycle specialist using explicit readiness rules without model tokens. Jev would be an optional natural-language intent classifier, not a replacement for prerequisite gates, specialist reasoning or human review.

A future small experiment could classify 30–50 labeled requests into trial search, literature search, visualization, analysis, or needs-deeper-reasoning. Separate development and held-out examples; include ambiguous and multi-intent requests. Compare the existing approach with Jev on route correctness, fallback frequency, total latency and total cost, including the extra routing request. Keep lifecycle gates deterministic and validate every selected destination. Only expand the experiment if it shows a useful quality/cost tradeoff; a small pilot alone does not establish deployment reliability.

Revisit when routing consumes repeated standalone model calls, or a programmatic entry point can execute simple requests without a larger-model turn. Merely adding Jev after an agent already interprets the request is not evidence of savings. No SDK, key, API call or installed-skill change is needed while deferred.

References: [TypeSafe quick start](https://docs.typesafe.ai/introduction/quickstart), [role within applications](https://docs.typesafe.ai/introduction/coding-agents), [documented model limitations](https://docs.typesafe.ai/model-jaggedness/jev-1.13).

Define routine eligible tasks and conditions that require deeper analysis. Missing prerequisites, unresolved causal identification, contradictory evidence and failed review should trigger escalation. Make budgets and stop conditions explicit. Use configurable policies rather than an unsupported promise that a fast model is adequate.

Acceptance: compare the proposed router against a consistently careful baseline on reserved cases. Report quality failures, escalation frequency, latency and cost. Adopt routing only when its quality/cost tradeoff is acceptable; never skip statistical review to meet a budget.

## 6. Package and document the validated result

Document which capabilities are implemented, experimental or still planned. Update installation paths and metadata only when the runtime and distribution approach are settled. Keep upstream credits/license. Add a synthetic end-to-end demonstration that can be reproduced from a fresh checkout.

Acceptance: existing skill-only usage still works, installation can be tested in isolation, and the demonstration includes logs, artifacts, review output and environment information.

## Decisions before implementation

- Build a repeatable behavioral evaluation baseline using the existing routing examples and synthetic studies, including expected evidence and prohibited conclusions.
- Select the host executor, model/version and evaluation budget for actual specialist runs.
- Keep the current local runtime and MCP handoff contract; add infrastructure only for demonstrated use cases.
- Revisit optional Jev intent routing only after measuring a bottleneck; Laya is outside the current scope.

Next candidates: structured model-based evaluation cases, a review UI and checkpoint/replay of external tool execution beyond the implemented reviewed-handoff checkpoints. The deterministic controller tests are not a replacement for evaluation of actual agent behavior.

## Broader RHC capability comparison

A fresh-agent pilot is evaluating original skills versus the upgraded bundle on identical RHC inputs, including visual reporting, actual MCP usage, and a cold-restart follow-up with ordinary file reuse versus structured memory. Unlike the earlier paired-script audit, this pilot records actual model token usage. Report cached input separately, preserve the common task prompt, and do not generalize one run per arm into a proven component-level efficiency effect. Local CSV import and a summary-bar template extend the server for this concrete use case.

The completed [fresh-agent RHC pilot](../../examples/rhc_agent_pilot/README.md) now includes both reports, fresh-session follow-ups, independent review and actual token telemetry. It demonstrated provenance and persistence, but no token savings or clear visual superiority. Prioritize a compact fingerprint-aware resume helper, scientific chart contracts, and replicated component ablations before efficiency claims.
