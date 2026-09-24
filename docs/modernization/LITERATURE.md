# PubMed and Europe PMC literature connectors

The optional local MCP server now exposes 14 tools, including four literature operations. They retrieve citations and available abstracts, preserve source snapshots, and build traceable reference lists. They do not appraise evidence, synthesize treatment effects, download full-text articles, or write confirmed project memory.

## Tool contracts

| Tool | Inputs | Output |
|---|---|---|
| `search_literature` | `provider` (`pubmed` or `europepmc`), native query, `page_size` 1–20 | Compact citations, source total, snapshot ID, next-page indicator |
| `next_literature_page` | Saved search artifact ID | Next page using the original provider/query and saved cursor or offset |
| `get_article` | Provider, article ID, optional Europe PMC source (default `MED`) | Full normalized citation and available abstract, source metadata and record URI |
| `build_reference_list` | 1–10 search/article artifacts | Identifier-grouped references as CSV, Markdown and canonical JSON |

Use a numeric PMID for PubMed. Europe PMC uses a source/ID pair, for example `MED` plus a PMID or `PPR` plus a preprint ID returned by search. IDs are validated before constructing URLs. Arbitrary URLs and full-text download endpoints are not exposed.

Search syntax belongs to each provider; queries are not assumed to mean exactly the same thing in both indexes. PubMed uses ESearch with relevance ordering, followed by one batched EFetch for the page's PMIDs. Europe PMC uses its REST search with `resultType=core`. Native query translations/warnings are saved where available. The default page size is 10; each chain stops after at most 10 pages. PubMed also respects the first-10,000-result ESearch boundary, though this connector's own page cap is much smaller.

Paging uses saved query/cursor state and can resume from the artifact store after a server restart. Europe PMC's unchanged final cursor means exhaustion; a cycle to an older cursor is rejected. PubMed uses offsets. Neither is advertised as a transactionally frozen index; updates and ranking changes can produce gaps or duplicate records across pages.

## Record fidelity and provenance

Each search/article artifact saves raw provider responses plus `literature.json`. PubMed search snapshots include both `search.json` and `records.xml`. Europe PMC snapshots include `response.json`. Manifests record provider, request URL, individual UTC retrieval times, SHA-256 checksums and query/page context. No API credentials are stored.

Normalized records retain:

- PMID, PMCID, normalized DOI, provider source/ID and source URL.
- Title, authors, journal, source publication date and publication types.
- Available abstract sections; PubMed section labels are preserved and Europe PMC HTML markup becomes plain text.
- Source correction/retraction metadata, copyright/license and open-access indicators when supplied.
- NCT IDs explicitly mentioned in the returned title, abstract or PubMed databank accession fields.

An NCT mention is a retrieval clue, not proof that the article is the primary trial report. A match may be a follow-up, protocol, commentary or article that mentions several trials. PubMed can report a retraction through publication types or `RetractionIn`; otherwise its normalized retraction indicator stays unknown. Europe PMC's explicit Y/N indicator is retained when present. These flags are source observations, not a complete independent retraction check or peer-review assessment. Preprints remain identifiable through their source and publication types.

Missing abstracts remain empty lists. Dates retain source precision and can differ legitimately between providers (electronic publication versus journal issue date). Invalid/unrecognized DOI or PMCID strings are not used as deduplication keys; original values remain in raw snapshots. PubMed primary article IDs are read from the article's own ID list, excluding IDs of cited references. PubMed books are supported as citation records.

Resources:

- `biostat://artifacts/{artifact_id}/literature`: normalized records, including available abstracts.
- `biostat://artifacts/{artifact_id}/references`: reference-list JSON with every source variant.
- Existing artifact manifest resources also apply. Raw JSON/XML files remain in the local artifact directory.

Tool search responses omit abstracts to keep routine context compact; `get_article` or resource reads retrieve the detailed record. This is selective retrieval, not measured token savings.

## Duplicate handling

Records are grouped using exact PMID, PMCID or normalized DOI, plus the provider's native source/ID. Matching is transitive across these identifiers. Titles alone never trigger merging. A shared DOI/PMCID that would connect different PMIDs causes `identifier_conflict` and requires inspecting the records rather than silently collapsing them.

A grouped reference retains **all source records**. Differences in title, DOI, date, publication types or retraction indicators are listed explicitly, not overwritten. The display title comes from the first input record; canonical JSON retains the alternatives. Source query, page, retrieval date and raw-response hashes remain attached through input provenance.

Outputs are `references.md` (readable linked citation table), `references.csv` (identifiers, source names, trial mentions and metadata differences), and `references.json` (all normalized source variants, including abstracts). Spreadsheet-formula-like titles are escaped in CSV; canonical JSON preserves the original text. A list supports at most 200 source records from 10 artifacts and is explicitly limited to selected snapshots, not a systematic review.

## Transport and source access

No additional dependency or API key is needed for this first increment. Only the configured NCBI E-utilities and EMBL-EBI Europe PMC HTTPS endpoints are accepted. Redirects and responses above 5 MiB are refused. Existing bounded timeouts and at most two attempts apply. PubMed requests, including retries, are spaced at least 0.36 seconds apart within one server process; Europe PMC requests at least 0.2 seconds. Multiple processes sharing an IP are not coordinated by this local limiter. High-volume deployment needs a shared limiter and source-specific configuration.

XML is parsed without fetching its external DTD; entity declarations and unsupported encodings are rejected. Provider error payloads, malformed records, mismatched IDs, missing articles and modified saved artifacts produce structured tool errors. There is no fallback from a live-source failure to fixtures.

Abstracts may be copyrighted. The server preserves supplied rights information and includes the [NCBI disclaimer and copyright notice](https://www.ncbi.nlm.nih.gov/About/disclaimer.html) in result metadata. Full-text retrieval is not implemented, and open-access metadata is not a blanket license to redistribute content.

## Demos and use

With the existing `.[mcp]` installation:

```sh
# Synthetic fixture; actual MCP subprocess, no network
.venv/bin/python -m biostat_mcp.literature_demo --output outputs/literature-demo

# Live trial record, two literature sources, pages, article details and reference list
.venv/bin/python -m biostat_mcp.literature_demo --live --output outputs/literature-live-demo

.venv/bin/python -B -m unittest discover -s tests -v
```

The live demo retrieves trial `NCT03548935`, searches its identifier in both sources, fetches at most two pages of three citations per provider, and retrieves PMID `33567185` from each provider to demonstrate overlap. It reads detailed records and the final reference resource through MCP. It records all calls and manifests in `run.json`. The chosen identifier is a technical demonstration, not an exhaustive semaglutide or obesity search strategy.

The offline demo requires `--offline --demo-literature` on the server (plus `--demo-trials` for the trial-linked workflow). Fixtures are synthetic and clearly labeled, use package provenance and omit live article links. They implement a small predictable query subset for testing, not complete provider search grammars. Live and synthetic artifacts cannot be combined.

Example for a newly started server in Codex:

> Use biostat to retrieve trial NCT03548935, search its identifier in PubMed and Europe PMC, fetch two pages from each, and build a reference list. Preserve duplicate-source provenance and report any conflicting metadata. Treat NCT mentions as candidate links, not verified trial reports.

The existing editable server registration is sufficient; a fresh process loads the expanded tools. An already running server needs restarting/reloading. No installed skill or global host configuration is modified by this increment.

## Validation and later work

See [LITERATURE_RESULTS.md](../../examples/mcp/LITERATURE_RESULTS.md) for actual live counts, checksums, tests and exact changed files. The tests run without network access and include a real stdio protocol roundtrip with synthetic provider responses.

An explicit reviewed handoff of selected source/artifact references into workflow state and confirmed project memory is now implemented; see [REVIEWED_HANDOFF.md](REVIEWED_HANDOFF.md). Source retrieval alone must not mark an estimand, identification argument or result as reviewed. Full-text adapters, evidence appraisal, systematic-review screening, model routing and token/cost evaluation remain separate work.

Primary documentation: [NCBI E-utilities parameters](https://www.ncbi.nlm.nih.gov/books/NBK25499/), [NCBI usage guidance](https://www.ncbi.nlm.nih.gov/books/NBK25497/), [Europe PMC REST API](https://europepmc.org/RestfulWebService). Endpoint behavior was verified directly against both official APIs.
