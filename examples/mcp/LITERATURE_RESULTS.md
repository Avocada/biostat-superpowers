# Literature connector validation

Validated 2026-09-24T01:13:11.517673+00:00 (UTC), Python 3.11, official MCP SDK 2.2.0.

## Results

- **105 tests passed**, zero skipped in the MCP environment: 83 previous tests plus 22 literature tests.
- Live MCP subprocess discovered all **14 tools** and performed trial retrieval, PubMed and Europe PMC search/pagination, article retrieval, record/resource reads and reference-list construction.
- Live search query: `NCT03548935`. Source-reported totals were **13 PubMed hits** and **64 Europe PMC hits** at retrieval. The demo selected two pages of three records per source; these totals are not expected to match because the indexes/search scopes differ.
- Two additional detail records retrieved PMID `33567185` from both sources. Its normalized DOI matched: `10.1056/nejmoa2032183`.
- **14 selected source records → 12 identifier-grouped references**, with every source variant and metadata difference preserved.
- Offline protocol demo: **8 synthetic source records → 4 references**, including a clearly identified preprint; no network calls or live fallback.
- The generated Markdown reference table was inspected for source links, duplicate grouping and trial-ID mention labeling. A hit can lack an NCT mention in the returned abstract because the provider searches additional indexed content.
- `git diff --check` passed; repository skill files were unchanged.

## Source snapshots

Each request is saved with a UTC timestamp and checksum; the live `run.json` contains its URL and artifact references.

| Provider | Operation | File | SHA-256 |
|---|---|---|---|
| pubmed | Search | search.json | `29aecc588871da73b535e1751297699288337b80f2ece29f1d75d35eb8fdde19` |
| pubmed | Search | records.xml | `82c32cbcea1540f0eab196528a768ae63836dedac869f4da2c013c9e6176e175` |
| pubmed | Search | search.json | `eec45597caf4e38092d8ed8b95a8883d896ab0222a7c04f1734632e4cad56a6b` |
| pubmed | Search | records.xml | `c4cf6e6a08281d5e97cfbde36e210d3d85426c51d514c4d76cda6dc4d13e825a` |
| europepmc | Search | response.json | `cb7dcb1eb925df96a4a38268f6fec28514cfcd8d2af47bd7a8a41836c3811fbc` |
| europepmc | Search | response.json | `efd6e5fec555df61e17a730b10b27ed43985f14b823174b139307bd0a2988874` |
| pubmed | Detail | records.xml | `b3cf6a18c3906c27475c4a49d31f5741bf40fa056afc62f07d07fa54dbff28c4` |
| europepmc | Detail | response.json | `337f1bc04ba2f1748f70b46b253ec9d3633dd66294dbdf94f406bca2727b2d7d` |

Generated outputs are ignored by Git:

- `outputs/literature-live-demo/run.json`: full live protocol run; the referenced artifact directory contains `references.md`, `references.csv`, and `references.json`.
- `outputs/literature-demo/run.json`: deterministic synthetic protocol example.

See [LITERATURE.md](../../docs/modernization/LITERATURE.md) for reproducible commands. Provider totals, ranking and metadata may change later; this run preserves the source bytes. This is a retrieval demonstration, not evidence appraisal, a systematic review, or a token-savings experiment.

## Exact files changed in this increment

Added:

- `biostat_mcp/literature.py`
- `biostat_mcp/literature_fixture.py`
- `biostat_mcp/literature_demo.py`
- `biostat_mcp/data/literature-demo.json`
- `tests/test_literature.py`
- `docs/modernization/LITERATURE.md`
- `examples/mcp/LITERATURE_RESULTS.md`

Updated:

- `biostat_mcp/core.py` — per-attempt request hook for rate limiting; literature artifact kinds.
- `biostat_mcp/server.py` — four literature tools, two resources and explicit fixture flag.
- `biostat_mcp/data/catalog.json` — PubMed and Europe PMC marked available with implemented scope.
- `docs/modernization/MCP_SERVER.md` — 14-tool inventory and updated source boundary.
- `docs/modernization/README.md` — literature guide link.
- `docs/modernization/ROADMAP.md` — implemented literature milestone.
- `docs/modernization/CLINICAL_TRIALS.md` — updated next-step reference.

No dependencies were added. Workflow/memory source, installed skills and global host configuration were unchanged. The existing server registration still applies; restart/reload an existing server process to discover new tools. No commit or push was performed.

Next: explicitly reviewed source/artifact handoffs into workflow state and confirmed project memory. Full-text retrieval, evidence synthesis, semantic matching, multi-process rate coordination, model routing and cost evaluation remain unimplemented.
