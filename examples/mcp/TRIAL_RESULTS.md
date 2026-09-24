# ClinicalTrials.gov implementation results

Validated 2026-09-24T00:52:54.538096+00:00 (UTC), Python 3.11, MCP SDK 2.2.0, vl-convert-python 1.9.0.post1.

## Executed checks

- Full test suite: **83 passed, zero skipped** with the MCP extras installed. This includes the previous 63 tests and 20 new trial tests.
- Live MCP subprocess: discovered all 10 tools, searched, paginated, retrieved a trial, read its raw record, generated a comparison, read comparison/figure resources, and rejected a malformed NCT ID.
- Offline MCP subprocess: explicitly synthetic fixture, four trials across two pages, same protocol flow, no network access.
- Trial chart PNG visually checked for readable labels, counts and an explicit selected-snapshot denominator.
- `git diff --check` passed; `git diff --name-only -- skills` returned no changes.

## Live demonstration

Query: condition `obesity`, intervention `semaglutide`, phase `PHASE3`; no status filter. The registry reported **77 matches**. The demo fetched two pages of five trials and compared **10 unique trials**. This is a selected subset, not all matches or a comprehensive GLP-1 review.

| Status | Trials in selected snapshots |
|---|---:|
| ACTIVE_NOT_RECRUITING | 3 |
| COMPLETED | 4 |
| NOT_YET_RECRUITING | 2 |
| RECRUITING | 1 |

Saved API response checksums:

- Search page 1: `8649a3913a887e3dedd1dce4b08d18a3aa57ada9e68d808224098ee46b12380e`
- Search page 2: `37898e269a63331fb99a4224b1b48ceb8330ced626fbac25282c94e4dcaf6858`
- Detail `NCT03552757`: `eda2a390e2af89ae45e3c4406e74a04c933d36cc789c2d3869593675426173af`

The complete live run is under ignored `outputs/trials-live-demo/run.json`; its comparison artifact directory contains CSV, JSON, Markdown, SVG, PNG and Vega-Lite. The synthetic run is under `outputs/trials-demo/run.json`. Regeneration instructions are in [CLINICAL_TRIALS.md](../../docs/modernization/CLINICAL_TRIALS.md). Registry updates and ordering can change later results; files preserve the bytes used in this run.

## Exact source/documentation changes in this increment

Added:

- `biostat_mcp/trials.py`
- `biostat_mcp/trials_demo.py`
- `biostat_mcp/data/trials-demo.json`
- `tests/test_trials.py`
- `docs/modernization/CLINICAL_TRIALS.md`
- `examples/mcp/TRIAL_RESULTS.md`

Updated:

- `biostat_mcp/core.py` — shared bounded transport and new artifact kinds.
- `biostat_mcp/server.py` — four trial tools, two resource templates and explicit synthetic mode.
- `biostat_mcp/data/catalog.json` — ClinicalTrials.gov now available.
- `tests/test_mcp.py` — assert existing tools remain available without freezing the discovery count.
- `docs/modernization/MCP_SERVER.md` — expanded capabilities and source boundary.
- `docs/modernization/README.md` — link to the trial connector guide.
- `docs/modernization/ROADMAP.md` — implemented trial milestone.

No dependencies were added. Existing workflow/memory source files and installed skills were unchanged. The existing Codex server registration remains in place; a fresh server process loads the new tools. No commit or push was performed.

Remaining work: literature connectors, explicit reviewed handoff to workflow state and confirmed project memory, larger-search/registry-change handling if needed, and real-model quality/cost evaluation. Numeric trial-result synthesis, meta-analysis and model routing are not implemented here.
