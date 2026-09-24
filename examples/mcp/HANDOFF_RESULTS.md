# Reviewed handoff validation

Validated 2026-09-24T01:24:39.828033+00:00 (UTC), Python 3.11, MCP SDK 2.2.0. All data and confirmations in this demo are explicitly synthetic. No actual user research decision or scientific result was approved.

## Results

- **129 tests passed**, zero skipped in the optional MCP environment: 105 previous tests plus 24 new handoff tests.
- The real MCP stdio demo discovered **19 tools**, retrieved a synthetic registry artifact, created an initial workflow, prepared proposals, read the review resource, retrieved context and inspected the audit history.
- Separate simulated host calls applied confirmations and reset state; no MCP approve/apply/reset tool exists.
- Memory-only confirmation preserved `estimand_ready=false` and the design route.
- A confirmed synthetic design result advanced to preparation, with memory and review provenance surviving database reopen.
- A changed source payload produced `artifact_changed` and no dispatch route. The synthetic source was restored after the probe.
- A reviewed input reset returned to design and withheld old input-bound memory.
- Additional tests exercised the entire seven-stage causal lifecycle, required ready evaluation, no-progress/fatal stops, host CLI inspect/apply, project isolation, exact-digest confirmation, repeated/competing approvals, transitive source fingerprints, memory deletion/correction, external memory exclusions and rollback after an injected failure between event insertion and checkpoint update.
- `git diff --check` passed; repository skill files were unchanged.

## Observed transitions

| Event | Next route | Context/result |
|---|---|---|
| Unconfirmed proposal | design | Required decision unavailable |
| Confirmed source-retention memory | design | Source decision available; readiness unchanged |
| Confirmed design result | preparation | Estimand available with approval/source references |
| Changed source bytes | blocked | Integrity failure prevents reuse |
| Reviewed new-input reset | design | Previous input-bound context withheld |

The demonstration produced `outputs/handoff-demo/REPORT.md`, `run.json`, review proposals and the ignored artifact-root `project-memory.sqlite3`. The audit records `memory_only`, `workflow_result` and `host_reset` events. Regenerate with:

```sh
.venv/bin/python -m biostat_mcp.handoff_demo --output outputs/handoff-demo
.venv/bin/python -B -m unittest discover -s tests -v
```

This is a deterministic integration test of review/checkpoint mechanics, not validation of real statistical reasoning, approval authentication or token/cost savings.

## Exact changes in this increment

Added:

- `biostat_mcp/handoff.py`
- `biostat_mcp/handoff_demo.py`
- `tests/test_handoff.py`
- `docs/modernization/REVIEWED_HANDOFF.md`
- `examples/mcp/HANDOFF_RESULTS.md`

Updated:

- `biostat_workflow/memory.py` — trusted atomic transaction hook; externally excluded stale-record IDs propagate to dependents during retrieval.
- `biostat_mcp/core.py` — reviewed-proposal artifact kind.
- `biostat_mcp/server.py` — five proposal/run/context/audit tools and review resource; no approval mutation tool.
- `docs/modernization/MCP_SERVER.md` — 19-tool inventory and implemented handoff status.
- `docs/modernization/README.md` — handoff guide link.
- `docs/modernization/ROADMAP.md` — checkpoint, memory and integration milestones.
- `docs/modernization/MEMORY.md` — adapter contract and remaining scope.
- `docs/modernization/WORKFLOW_CONTROLLER.md` — checkpoint extension relationship.
- `docs/modernization/CLINICAL_TRIALS.md` — implemented handoff link.
- `docs/modernization/LITERATURE.md` — implemented handoff link.

The controller algorithm, installed skills, repository domain-policy skills, global Codex configuration and dependencies were unchanged. The existing editable server registration loads these tools in a fresh server process. Changes remain uncommitted and unpushed.

Remaining work: authenticated review UX, deliberate specialist execution and behavioral evaluations, remote-source refresh policy, external-operation replay and retention/deletion across proposal/audit histories. Jev/Laya and fast/slow model routing remain undefined/unevaluated.
