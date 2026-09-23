# Proposed implementation roadmap

Status: planning only. Sequence is provisional pending the user's component priorities. No runtime framework, model provider or external service has been chosen.

## 1. Record the baseline and automate evaluation

Turn the existing routing examples into structured cases with expected specialist, required evidence and prohibited conclusions. Record model/version, prompt version, seed where supported, cost, latency, tool calls and outputs. Separate deterministic structural checks from model-dependent behavioral scores.

Acceptance: a repeatable command emits a per-case report; all eight routing categories are covered; causal overclaiming and leakage cases can fail independently of routing accuracy. Pin a baseline before comparing new features. Reserve unseen cases to limit tuning to the evaluation suite.

## 2. Define workflow state and execution

Define a versioned run record containing run ID, research question, estimand, phase, selected skill, input fingerprints, artifacts, review status, revision count and stop reason. Define transitions that retain the current skills' sequencing and review requirements. Start with a small local adapter instead of committing immediately to a graph framework.

Acceptance: a synthetic run demonstrates a normal path, a critique-triggered revision, a bounded failure and restart from a checkpoint without silently repeating completed work. Missing prerequisites prevent downstream execution. Logs explain each transition.

## 3. Add project-scoped memory

Separate durable user-confirmed decisions from run scratch space. Store each memory item's source, project/run association, creation time and revision/supersession metadata. Retrieve only relevant project records; detect changed data fingerprints and conflicting assumptions. Provide inspection, correction and deletion.

Acceptance: a later run can reuse a confirmed estimand with its provenance; changed input data invalidates dependent artifacts; contradictory decisions are surfaced; unrelated project memory is excluded. Do not put patient-level records into a default memory store.

## 4. Add optional MCP connections

Choose a first concrete tool only after confirming its use case, data boundary and authentication requirements. Define adapter contracts, timeouts, retry limits and audit events. Keep credentials outside committed files and treat tool-returned text as data. Maintain a local/mock path for development.

Acceptance: one mock-backed adapter demonstrates successful execution, malformed output, timeout and unavailable-service behavior. Any real-service integration gets an explicit configuration guide and a smoke test. No connector is required for the standalone skills to work.

## 5. Evaluate fast/slow decision routing

Define routine eligible tasks and conditions that require deeper analysis. Missing prerequisites, unresolved causal identification, contradictory evidence and failed review should trigger escalation. Make budgets and stop conditions explicit. Use configurable policies rather than an unsupported promise that a fast model is adequate.

Acceptance: compare the proposed router against a consistently careful baseline on reserved cases. Report quality failures, escalation frequency, latency and cost. Adopt routing only when its quality/cost tradeoff is acceptable; never skip statistical review to meet a budget.

## 6. Package and document the validated result

Document which capabilities are implemented, experimental or still planned. Update installation paths and metadata only when the runtime and distribution approach are settled. Keep upstream credits/license. Add a synthetic end-to-end demonstration that can be reproduced from a fresh checkout.

Acceptance: existing skill-only usage still works, installation can be tested in isolation, and the demonstration includes logs, artifacts, review output and environment information.

## Decisions before implementation

- Confirm the component priorities and what “Jev / Laya” refers to, if those names remain relevant.
- Decide whether the first runtime is a local command-line workflow or a service.
- Choose one real MCP use case and project-memory storage requirements.
- Choose models and evaluation budgets based on measured results.

Suggested first implementation task: create the structured evaluation cases and run-report format, then define the workflow-state contract. This gives the proposed memory and routing changes a measurable baseline.
