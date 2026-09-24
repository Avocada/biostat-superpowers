# Optional local MCP server

Implemented on `v2`: a small Python MCP server for dataset retrieval, profiling, exploratory visualization and ClinicalTrials.gov trial discovery/comparison. Existing domain skills, controller and memory remain independent. The server has no model dependency or API key requirement. It runs as a local stdio subprocess, not a public HTTP service.

## Architecture

```text
MCP host (Codex or another compatible client)
    │ initialize / tools/list / tools/call / resources/read
    ▼
biostat_mcp.server — official Python MCP SDK, typed tool inputs
    ▼
biostat_mcp.core — directly callable Python operations
    ├── curated UCI adapter → public metadata and CSV
    ├── bundled synthetic fixture and chart examples
    └── local artifact store → CSV, profile, Vega-Lite, SVG, PNG, manifests

Existing skills → scientific policy and review
Existing controller → lifecycle gates and termination
Existing memory → confirmed project decisions
```

This is an actual MCP implementation: a separate client discovers and invokes tools and reads resources over the protocol. The demo performs that exchange with a subprocess. A directory of links alone would not provide these operations. The server is not a subagent: it does not reason about an open-ended assignment or select scientific methods.

No LangGraph is needed. Transport is a thin wrapper around ordinary functions; the existing Python controller remains the workflow control layer. Retrieval operations do not automatically update workflow readiness or project memory. The reviewed-handoff adapter now prepares proposals; a separate host confirmation commits memory and an optional controller result atomically.

The ClinicalTrials.gov extension is documented in [CLINICAL_TRIALS.md](CLINICAL_TRIALS.md), including its four additional tools and protocol demo. The server now exposes nineteen tools. [REVIEWED_HANDOFF.md](REVIEWED_HANDOFF.md) documents project runs, review proposals and confirmed context. [LITERATURE.md](LITERATURE.md) describes the PubMed/Europe PMC extension.

## Available capabilities

| Tool | Input | Result |
|---|---|---|
| `list_datasets` | Optional text query | Three curated entries with availability |
| `fetch_dataset` | `demo`, `uci:53`, or `uci:45` | Saved snapshot and source manifest; no full dataset in tool response |
| `profile_dataset` | Dataset artifact ID | Types, roles, missingness and numeric summaries; saved profile |
| `list_chart_examples` | Optional text query | Three local templates and source links |
| `render_chart` | Dataset ID, matching profile ID, template, columns, optional title | SVG, PNG, Vega-Lite specification and provenance |
| `inspect_artifact` | Artifact ID | Manifest, checksums and local directory |
| `search_trials` | Condition/intervention, optional status/phase, page size | Saved ClinicalTrials.gov search page |
| `next_trial_page` | Search artifact ID | Next page using the saved query |
| `get_trial` | NCT ID | Trial details and raw record resource |
| `compare_trials` | Search/detail artifact IDs | Comparison table and status-count chart |
| `search_literature` | Provider, native query, page size | Saved citation/abstract snapshot and compact citations |
| `next_literature_page` | Search artifact ID | Next provider page with saved query |
| `get_article` | Provider and source/ID | Citation and available abstract |
| `build_reference_list` | Literature artifact IDs | Identifier-grouped references with all source variants |
| `create_project_run` | Project/run, goal, input fingerprint | Initial workflow checkpoint; no ready flags |
| `propose_reviewed_handoff` | Decision, sources, stages, optional workflow result | Unconfirmed hash-bound review proposal |
| `inspect_project_run` | Project/run | Checkpoint and validated next route |
| `get_project_context` | Project/run, required keys, byte budget | Confirmed source-validated memory for next stage |
| `inspect_handoff_audit` | Project/run | Accepted review and reset history |

Resources:

- `biostat://catalog`: 24 entries, clearly distinguishing available capabilities from reference-only links.
- `biostat://chart-examples`: project-authored histogram, scatter and boxplot examples.
- `biostat://artifacts/{artifact_id}/manifest`: saved result description.
- `biostat://artifacts/{artifact_id}/figure`: generated SVG, fetched only on request.

UCI support currently covers Iris and Heart Disease only. Discovery does not search the complete UCI repository. ClinicalTrials.gov search, detail retrieval and comparisons are implemented. PubMed and Europe PMC now support citation/abstract retrieval and reference lists. Genomic sources, books, other visualization galleries and external tool platforms remain catalog references. No books or galleries are bulk downloaded. The three templates are authored in this project using Vega-Lite grammar.

## Install and run

Python 3.10+; tested with Python 3.11. From the development checkout:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[mcp]'
.venv/bin/python -m biostat_mcp.demo
.venv/bin/python -m biostat_mcp.demo --dataset uci:53 --output outputs/mcp-uci-demo
.venv/bin/python -m biostat_mcp.demo --dataset uci:45 --output outputs/mcp-heart-demo
.venv/bin/python -B -m unittest discover -s tests -v
```

The default demo is offline and uses synthetic observations. UCI demos require outbound HTTPS. Each run records actual protocol calls and result manifests in `run.json`. Figures are under the chart's `local_directory`. UUIDs and retrieval timestamps vary; UCI data may change. Source checksums record the actual snapshot.

To run the server under any stdio MCP host, launch `.venv/bin/biostat-mcp --artifact-dir /absolute/project/outputs/mcp`. The host starts and stops the process. Running it directly waits for protocol input; it is not an interactive terminal program. Add `--offline` to disable UCI downloads.

The optional dependencies pin the official `mcp==2.2.0` SDK and `vl-convert-python==1.9.0.post1`; transitive dependencies are resolved by pip, not fully locked. Installing the base package without extras keeps workflow and memory usage dependency-free. MCP tests skip when extras are absent; the full validation environment must install them.

## Connect to Codex

A reviewed configuration example is in [codex-config.example.toml](../../examples/mcp/codex-config.example.toml). Replace the absolute path placeholder and merge the section into your host configuration. Alternatively, on this machine:

```sh
codex mcp add biostat -- /Users/amiee/Projects_code/biostat-superpowers/.venv/bin/biostat-mcp --artifact-dir /Users/amiee/Projects_code/biostat-superpowers/outputs/mcp
codex mcp list
```

These are setup instructions, not commands the implementation automatically executes. Global Codex settings and installed skill links were left unchanged. The MCP subprocess test demonstrates protocol compatibility, not that the current Codex session has loaded these tools. Consult the [official Codex MCP guide](https://learn.chatgpt.com/docs/extend/mcp?surface=cli) for host configuration. Use an artifact directory appropriate to each project to avoid sharing results unintentionally.

## Data and operation contracts

Successful tool calls return `{ "ok": true, "result": ... }` as structured content and a JSON text fallback. Expected operational failures set MCP `isError` and return `{ "ok": false, "error": { "code", "message", "retryable" } }`. SDK validation rejects arguments that do not match tool input schemas. Resource failures use protocol resource errors.

Sources are restricted to bundled content and the configured UCI, ClinicalTrials.gov, NCBI E-utilities and EMBL-EBI Europe PMC HTTPS hosts; dataset URLs must match the selected ID exactly and redirects are refused. No arbitrary local filenames, URLs, user-provided chart programs or SQL are exposed. UCI requests use a 10-second socket timeout, a checked 15-second read deadline and at most two attempts for connection errors, rate limiting and server failures. The deadline is checked between reads, not a hard wall-clock cancellation. CSV/metadata downloads are capped at 5 MiB; CSVs at 20,000 rows and 100 columns. There is no credential store or remote upload operation.

Snapshots are append-only through the API. Atomic directory publication avoids partially published artifacts; SHA-256 checks detect changed payloads before reuse. Manifests are local files, not signed attestations: this is reproducibility tracking, not protection against a user who can rewrite the whole store. There is no automatic retention cleanup or total disk quota yet.

Missing tokens are explicitly recorded (`empty`, `?`, `na`, `n/a`, `null`, `nan`, case-insensitive). Original CSV bytes are preserved. Metadata takes precedence over numeric inference, so numerically coded categories do not automatically become continuous variables. Inferred types still require review. Plots exclude only rows missing a selected axis and report the count. Original datasets are not imputed or overwritten. Boxplot whiskers use 1.5 IQR; grouped charts allow at most 20 categories.

Rendering requires a profile tied to the same dataset artifact, data hash and source-metadata hash. Only chosen columns enter inline chart data. The renderer disallows external data URLs. All outputs remain `exploratory_unreviewed`; a profile is not a scientific validation gate. A scatter plot cannot establish causation, and these tools do not replace estimand definition, missing-data analysis, causal identification or method evaluation in the existing skills.

## Context efficiency

Dataset rows and image bytes stay in artifact files unless explicitly requested. The model normally receives summaries and references. That can reduce context use compared with pasting complete datasets, but MCP itself does not compress conversation history or route between models. This implementation does not claim a measured token or cost reduction. Resource descriptions, tool schemas and responses also consume context.

## Validation and remaining work

See [RESULTS.md](../../examples/mcp/RESULTS.md) for the actual run record. Tests cover offline behavior, malformed sources, URL boundaries, bounded retries, artifact changes, types, missingness, profile matching, all chart templates and a real stdio client/server roundtrip. Live UCI tests are explicit demos, not network-dependent unit tests.

Later increments:

1. ClinicalTrials.gov and PubMed/Europe PMC retrieval are implemented; reviewed workflow/memory handoffs are implemented; a review UI and behavioral evaluation remain.
2. Evaluate existing ToolUniverse/BioMCP integrations before duplicating specialized genomic adapters. Add credentials only for chosen sources that need them.
3. Searchable reference/gallery metadata, respecting each source's access and reuse terms; use ordinary links where remote operations add no value.
4. Reviewed artifact handoffs now connect to workflow checkpoints and confirmed memory. Extend host review UX and evaluate real specialist behavior; do not store raw participant rows in decision memory.
5. Add retention, durable run/audit logs, checkpoint/restart and deployment configuration if usage requires them. Remote multi-user hosting needs a separate authentication and isolation design.
6. Evaluate real-agent task quality, latency and token cost. Jev (TypeSafe AI) routing is optional and deferred pending measured benefit; MCP does not implement it. See [ROADMAP.md](ROADMAP.md).

Sources: [official MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk), [UCI repository client/API usage](https://github.com/uci-ml-repo/ucimlrepo), [local Vega-Lite renderer](https://github.com/vega/vl-convert/tree/main/vl-convert-python).
