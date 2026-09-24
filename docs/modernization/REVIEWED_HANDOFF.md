# Reviewed sources → project memory → workflow state

This increment connects the optional MCP artifact store to the existing SQLite project memory and Python workflow controller. It creates durable, versioned checkpoints for **accepted handoffs**, not an autonomous statistical analyst. Existing installed skills and repository domain-policy files remain unchanged.

## Two distinct decisions

1. **Memory-only confirmation:** approve a concise source-grounded decision or finding for reuse. Memory is saved, but no workflow readiness flag changes.
2. **Workflow-result confirmation:** approve a result from the currently routed specialist. The existing controller validates and applies the result. Only that route's gate can advance; preparation still requires an explicit missingness assessment, causal identification remains required, and reporting remains behind a ready method-evaluation result.

Neither retrieval, a source's claimed quality, nor a proposal creates confirmed memory. A trial-ID mention remains a candidate link until actually reviewed. A literature list is not sufficient evidence that an estimand is defined or causal identification is established.

```text
retrieved artifact snapshots
    ↓
MCP proposal: summary + sources/hashes + project/run/version + optional Result
    ↓                         no durable decision/readiness change yet
host reviews exact proposal under existing specialist skill
    ↓
explicit confirmation referencing proposal SHA-256
    ↓                         single SQLite transaction
confirmed MemoryItem + reviewed event + versioned workflow checkpoint
    ↓
source/fingerprint/dependency checks → bounded context for next specialist
```

## MCP surface

The server exposes 19 tools: the previous 14 plus:

| Tool | Purpose |
|---|---|
| `create_project_run` | Create a project/run/goal with a host-supplied input fingerprint; starts at design with all readiness flags false |
| `propose_reviewed_handoff` | Save an unconfirmed proposal and readable review artifact; optionally propose a typed controller result |
| `inspect_project_run` | Inspect checkpoint, version, evidence issues and next route |
| `get_project_context` | Retrieve confirmed, current, stage-applicable memory with provenance and a byte budget |
| `inspect_handoff_audit` | Inspect accepted handoff and reset events, confirmations and before/after states |

`biostat://artifacts/{artifact_id}/handoff` exposes a proposal and its checksum. The proposal contains `review_skill` for a proposed workflow result, so the host can load the existing skill policy. No statistical expert instructions are duplicated in the adapter.

**There is no MCP approve/apply/reset tool.** The agent can prepare a proposal but cannot promote it merely by filling in a `confirmed_by` string in an MCP call. Confirmation is a separate host operation, described below. A user interface can call the same host API after obtaining explicit approval of a concrete proposal.

## Reviewable proposal

A proposal includes the project and run, expected run version, input fingerprint, a short memory key/summary, applicability stages, memory dependencies, optional superseded memory ID, source artifact IDs and hashes, the proposed result, and before/after state. Limits: 1–8 direct source artifacts, at most 40 snapshots including upstream dependencies, and a 4,000-character summary.

Source bindings include raw payload integrity plus complete manifest hashes. Derived profiles/charts, trial comparisons and literature reference lists bind their upstream artifact dependencies as well. Sources and proposal bytes are checked before applying and when reusing gate evidence/context. Updating a provider's website does not automatically change a stored snapshot: fetch a new snapshot and explicitly review a replacement. This adapter does not poll remote sources.

Use `outcome=null` (or omit it) for memory-only proposals. For workflow results use existing controller outcomes `complete`, `blocked`, `revise`, `fatal`. Optional result fields retain their existing restrictions: evaluation rating only at method evaluation; `missing_data_required` on completed preparation; a revision targets a valid upstream owner. A proposal cannot skip ahead by requesting a later stage.

Artifacts remain append-only through the API and retain `exploratory_unreviewed` status. Approval applies to the exact **decision/result**, not a blanket endorsement of every source. Proposal manifests remain immutable and say unconfirmed; the authoritative record that a proposal was subsequently accepted is its audit event.

## Host confirmation

A host or human first inspects the proposal:

```sh
.venv/bin/python -m biostat_mcp.handoff --artifact-dir /absolute/project/outputs/mcp inspect PROPOSAL_ID
```

After actual review and explicit confirmation of that exact proposal:

```sh
.venv/bin/python -m biostat_mcp.handoff --artifact-dir /absolute/project/outputs/mcp apply PROPOSAL_ID \
  --accept-digest SHA256_FROM_REVIEW \
  --reviewer REVIEWER_REFERENCE \
  --confirmation-ref ACTUAL_CONFIRMATION_REFERENCE \
  --review-notes 'What was reviewed and why this decision/result is accepted'
```

These placeholders must be replaced with actual review information. Do not invent reviewer identities or confirmation references, or run this merely because source retrieval succeeded. The implementation demo only uses clearly marked synthetic attestations and does not approve any real study finding.

The CLI/API records an **attestation**, not authenticated identity or proof that scientific review occurred. An actor with shell access and permission to edit the database can call it or alter files. The separation from the MCP tool surface is not a security boundary against that actor. A production host must enforce its own authorization/UI policy; signed approvals and multi-user authentication are not implemented.

The Python host API is `HandoffService.apply(proposal_id, expected_digest, reviewer=..., confirmation_ref=..., review_notes=...)`. No supplied path or SQL is accepted through MCP memory tools. The database is fixed to `project-memory.sqlite3` within the server's configured artifact root. Explicit project IDs scope memory and run lookups but do not isolate users who can read that database.

## Atomicity, corrections and stale evidence

Applying a proposal records the memory item, review event and workflow checkpoint in **one SQLite transaction**. The run version must still match the reviewed proposal. Competing or repeated applications fail; a failed transaction leaves none of the three writes behind and can be retried. The original `MemoryStore.record` now supports a trusted `transaction_hook` for this purpose. It is not callable through MCP arguments.

An accepted decision is bound to its exact proposal and audit event. Simply inserting a memory record that points to an unapproved proposal is insufficient for this adapter's context retrieval. Accepted summaries and keys must match the proposal. Records imported through the older direct MemoryStore API remain available there, but this stricter adapter withholds them until they have a valid reviewed handoff.

Corrections use a fresh reviewed proposal with `supersedes=old_item_id`. Existing memory logic atomically supersedes the old record and invalidates dependents. Conflicting active values are rejected by handoff application. If a correction would invalidate a completed workflow gate, include an appropriate `revise` result; otherwise the entire correction rolls back. Revision removes affected and downstream gate bindings using the controller's existing invalidation order.

Missing/deleted/invalidated gate evidence, a changed source payload/manifest, or an input mismatch blocks dispatch. `inspect_project_run` returns `usable=false`, the reason and no next route. It retains the historical state rather than silently rewriting what was previously approved. Hosts must check `usable`; using the old raw state directly with `controller.route` bypasses this adapter's evidence checks.

A host-only conservative reset handles stale evidence or a changed input contract:

```sh
.venv/bin/python -m biostat_mcp.handoff --artifact-dir /absolute/project/outputs/mcp reset \
  --project-id PROJECT --run-id RUN --expected-version CURRENT_VERSION \
  --input-fingerprint NEW_INPUT_AND_CONTRACT_FINGERPRINT \
  --reviewer REVIEWER_REFERENCE --confirmation-ref ACTUAL_CONFIRMATION_REFERENCE \
  --reason 'Reviewed reason for resetting the workflow'
```

Reset clears all readiness gates and loop counters, returns to design, increments the run version and records an audit event. It does not delete memory or automatically authorize further work. Old input-bound or source-stale records are withheld on retrieval; their historical rows remain inspectable. This is intentionally a host action, never automatic retry behavior.

## Reusing context

`get_project_context` determines the next specialist from the current state, filters by project/goal/stage/input fingerprint, validates proposal approvals and source integrity, and checks transitive dependencies. Caller-specified `required_keys` must all be available; optional records fill the remaining budget. Missing, stale, conflicting or over-budget required context returns `usable=false` and issues, rather than silently dropping a needed decision.

The budget is **UTF-8 bytes**, explicitly not tokens. Existing memory also accepts tokenizer callbacks through its Python API. No token or cost improvement is claimed by this demo.

An accepted record may be reused in another run of the same project/goal with the same input fingerprint and synthetic/live mode. This only supplies context: the new run still starts at design. Synthetic and live sources cannot be mixed. Raw participant rows, full abstracts and transcripts are not automatically copied into memory; only the proposed summary and references/confirmation metadata are stored. Sensitive-data classification of user-provided summaries is still the host's responsibility.

The host must continue loading the unchanged orchestrator and routed specialist skill. This increment does not supply an LLM executor or automatically call the specialist. Existing `MemoryExecutor` remains available for direct Python workflows, but it does not perform this adapter's artifact/audit checks; use this handoff context/state interface when those checks are required.

## Demo and validation

```sh
.venv/bin/python -m biostat_mcp.handoff_demo --output outputs/handoff-demo
.venv/bin/python -B -m unittest discover -s tests -v
```

The demo uses real MCP stdio with synthetic registry data and separately simulated host confirmations. It demonstrates:

1. Unconfirmed proposals leave memory empty and readiness unchanged.
2. A confirmed source-retention decision becomes reusable context while design remains pending.
3. A confirmed synthetic design result advances to preparation and survives reopening the database.
4. Altered source bytes block gate reuse; the fixture is restored after the probe.
5. An explicitly reviewed input reset returns to design and withholds old input-bound context.

[HANDOFF_RESULTS.md](../../examples/mcp/HANDOFF_RESULTS.md) records the executed checks and exact files changed. The existing MCP registration points to this editable checkout; a newly started server loads the five new tools without re-registration.

## Scope still deferred

This is a versioned **reviewed-handoff checkpoint**, not checkpoint/replay of external tool side effects or a full autonomous research run. Future work includes a review UI/authenticated host, deliberate automatic specialist execution with behavioral evaluations, source-refresh policies, artifact/memory retention and deletion across audit/proposal backups, and measured model/context routing. Existing direct memory deletion does not erase the separate proposal/event history; privacy-sensitive deployments need an explicit retention/deletion policy before use. No installed skills or model settings were changed.
