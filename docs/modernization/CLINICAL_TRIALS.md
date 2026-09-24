# ClinicalTrials.gov MCP connector

The local server now supports ClinicalTrials.gov API v2. It adds four tools to the six existing dataset/visualization tools, keeping installed skills and the workflow/memory packages unchanged. No additional Python dependency, API key or hosted service is required.

## Tools and workflow

1. `search_trials(condition, intervention, status, phase, page_size)` returns one page of compact trial summaries and a saved search artifact. Search condition/intervention use the registry's search semantics. Status and phase are exact enum filters. Phase uses `filter.advanced=AREA[Phase]...`, not an invented `filter.phase` parameter. Page size is 1–20 (default 10).
2. `next_trial_page(search_artifact_id)` uses the saved query and opaque pagination token. Callers cannot accidentally change filters while reusing a token. A chain is limited to 10 pages; reduce or narrow the search for larger needs.
3. `get_trial(nct_id)` retrieves design, enrollment count and ACTUAL/ESTIMATED designation, eligibility, primary outcomes/time frames, locations, last update and posted-results availability. The complete registry response, including any `resultsSection`, is preserved. Numeric results are not extracted or synthesized by this increment.
4. `compare_trials(artifact_ids)` takes 1–10 saved search/detail artifacts, deduplicates up to 100 unique trials and creates a comparison table plus a recruitment-status chart. It performs no new network calls. Different normalized records with the same NCT ID cause a `snapshot_conflict` instead of silently selecting a version.

All trial operations return the same success/error envelope as the existing tools. Inputs have MCP-generated schemas and validation. Invalid IDs, unsupported filters, malformed responses, missing records, offline requests, pagination limits and changed artifact payloads return structured errors.

Accepted phases: `EARLY_PHASE1`, `PHASE1`, `PHASE2`, `PHASE3`, `PHASE4`, `NA`. Mixed-phase studies can match a selected phase. Status examples: `RECRUITING`, `NOT_YET_RECRUITING`, `ACTIVE_NOT_RECRUITING`, `COMPLETED`, `TERMINATED`, `WITHDRAWN`. The complete accepted status set is in `biostat_mcp/trials.py`. No status filter means all source statuses, not recruiting studies only.

## What is saved and how to interpret it

Search/detail artifacts contain the exact API bytes in `response.json` and normalized data in `trials.json`. Their manifests include source URL, UTC retrieval timestamp, SHA-256 and, for searches, query, page number, source-reported total and whether another page is available. Source text remains untrusted data.

Comparison artifacts contain:

- `comparison.csv`: all normalized fields, including design, eligibility and primary outcomes; nested fields are serialized JSON. Cells that could be spreadsheet formulas are escaped.
- `comparison.json`: canonical unescaped field values plus input provenance and status counts.
- `comparison.md`: a compact overview with trial links, status, phase, enrollment and results availability.
- `chart.vl.json`, `figure.svg`, `figure.png`: locally rendered recruitment-status counts.

The chart denominator is **the unique trials in the supplied snapshots**. It is not automatically the entire search, all GLP-1 drugs, all obesity trials or a systematic review. A semaglutide keyword query is a demonstration, not an exhaustive GLP-1 search strategy. Pagination order and registry contents can change between requests; we record and deduplicate pages but do not claim a transactional snapshot of the registry.

Missing fields remain null/empty rather than being invented. An absent `hasResults` stays unknown, and `false` means no posted results indicated by the retrieved record. Neither implies treatment failure. Estimated enrollment is not pooled with actual enrollment; the count chart counts trials, not participants. Registry status and timestamps are source-reported and may lag reality.

New resources:

- `biostat://artifacts/{artifact_id}/trial-record`: complete search/detail API response, including any posted results.
- `biostat://artifacts/{artifact_id}/trial-comparison`: full comparison JSON.
- Existing manifest and SVG figure resources also work for trial artifacts.

API responses are capped at 5 MiB. Both adapters share the existing bounded HTTP transport (socket timeout 10 seconds; read deadline checked between reads; at most two attempts for connection errors/429/5xx). Redirects are refused; only the configured HTTPS host and study endpoints are accepted. Reduce `page_size` if a response exceeds the byte limit. A live error never silently falls back to synthetic data.

The synthetic fixture is explicitly enabled with **both** `--offline --demo-trials`. Its records and provenance are marked synthetic, with no links from placeholder NCT IDs to real studies. It implements simple substring filters for testing, not the complete registry search grammar. Synthetic and live artifacts cannot be combined.

## Run the demo

From the repository checkout with `.[mcp]` installed:

```sh
# Completely synthetic, but uses real MCP client/server communication
.venv/bin/python -m biostat_mcp.trials_demo --output outputs/trials-demo

# Real registry: phase-3 semaglutide/obesity search; two pages of five trials
.venv/bin/python -m biostat_mcp.trials_demo --live --output outputs/trials-live-demo

# Existing and new tests; unit tests do not contact the registry
.venv/bin/python -B -m unittest discover -s tests -v
```

The demo discovers tools, searches, retrieves the next page and one full trial, reads the raw record resource, compares the selected pages, reads the comparison and figure resources, and checks rejection of an invalid ID. `run.json` records calls and returned manifests. The real-source run requires outbound HTTPS.

The existing `biostat` registration points to this editable checkout, so a newly started server uses these tools without another installation. An already running host process needs to reload/restart the server; use a new Codex task to discover the updated tool set. The server is not silently modifying host configuration or installed skills.

Example prompt:

> Use biostat to search ClinicalTrials.gov for phase-3 semaglutide studies in obesity. Fetch the first two pages, retrieve a full trial record, and create a comparison table and recruitment-status chart. State the number retrieved versus the source-reported total.

## Validation and next increments

[TRIAL_RESULTS.md](../../examples/mcp/TRIAL_RESULTS.md) records the executed demos, test count and exact changed-file list.

The MCP server handles retrieval and descriptive presentation only. Existing skills still own study-design interpretation, estimands, missing-data methods and statistical review. The controller's readiness state and confirmed project memory are not changed by a successful API call. PubMed/Europe PMC retrieval is now implemented; see [LITERATURE.md](LITERATURE.md). The [reviewed handoff adapter](REVIEWED_HANDOFF.md) now connects explicitly approved source decisions/results to workflow state and confirmed memory. No model routing or token-savings claim is added.

API references: [ClinicalTrials.gov v2 API](https://clinicaltrials.gov/data-api/api), [official migration guide and pagination](https://clinicaltrials.gov/data-about-studies/api-migration), [study data structure](https://clinicaltrials.gov/data-api/about-api/study-data-structure). Actual query/filter behavior was also verified against the live v2 endpoint during implementation.
