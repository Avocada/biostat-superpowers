# Bounded protein and target evidence tools

The optional MCP server now adds two evidence operations for public human gene symbols and Ensembl identifiers. These are live connectors, not a generic omics analysis engine.

- `annotate_proteins(symbols)`: 1–10 plain gene symbols; reviewed human UniProt entries, protein/Ensembl identifiers and Reactome cross-references. Multiple matches remain explicit. At most five matches/symbol and twenty pathway annotations/match enter the summary; raw returned JSON is saved. A result count of five flags possible truncation. No pathway enrichment test is performed.
- `get_target_evidence(ensembl_id)`: a validated unversioned human Ensembl gene identifier; Open Targets tractability and the first ten drug/clinical candidate rows in the response. The provider's total count and raw response are retained. These records span all indications and modalities. They can include diagnostic imaging agents, multi-target drugs, withdrawals or advanced trials; they do not establish renal-cancer efficacy or approval.

All calls save immutable `omics_evidence` artifacts with source URLs, timestamps, request/response payloads and checksums. Responses remain `exploratory_unreviewed`. Retrieval hashes pin the returned bytes, not a named upstream release. The built-in memory API is separate: callers must verify source artifacts and correctly attribute review; none of these calls approves a scientific decision.

Only fixed UniProt and Open Targets HTTPS endpoints are reachable through these operations. Callers cannot supply arbitrary URLs, query programs, local paths, credentials or patient matrices. Offline mode rejects network operations. Download size is capped at 2 MiB. UniProt uses the existing bounded transport/retry rules; Open Targets POST has a 20-second socket timeout and no automatic retry. Provider errors are surfaced, not converted into empty biological evidence. The POST timeout is a socket timeout, not a guaranteed total wall-clock deadline. Response summaries are bounded; retain raw artifacts for complete returned annotations.

The current Open Targets API exposes `drugAndClinicalCandidates`; the older `knownDrugs` field was rejected during preflight. A live CA9 query confirmed the revised schema before the experiment. Tests use fixtures for deterministic behavior and an actual stdio roundtrip for the offline guard; live-source success is checked separately and is not guaranteed by unit tests.

The CCRCC study's full processed matrices were downloaded by the host from LinkedOmics, with metadata from the public CPTAC maintainer index. They were not passed through generic CSV import (5 MiB/100 columns), and this extension does not add a PDC downloader, whole-matrix backend, UniProt ID-mapping job service, Reactome enrichment service or exhaustive Open Targets search. Scientific inference and figures still run in local Python/R.

Primary interface documentation: [UniProt API](https://www.uniprot.org/help/api), [Open Targets API](https://platform-docs.opentargets.org/data-access/graphql-api). For systematic target-wide work, use the provider's bulk datasets rather than thousands of single-target queries.
