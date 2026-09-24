# Kidney-cancer proteogenomics: two configurations

Completed 2026-09-24. [Open the comparison](index.html), [independent review](independent_review.md), or [corrected upgraded follow-up](post_review/followup_corrected.html).

Both configurations produced matching, independently checked numerical analyses and successfully continued in a fresh session. The upgraded bundle demonstrated structured decision retrieval and evidence provenance, **not token savings or superior scientific results**. Jev was excluded.

**Correction:** the frozen upgraded follow-up prose and figure incorrectly say VEGFA protein n=1 in both cohorts. Correct counts are **1 all-stage / 0 early-stage**. Its tables were correct, and neither cohort was tested. The clearly separated [post-review companion](post_review/README.md) fixes the prose and regenerates the plot label from saved result rows, without refitting. The associated memory summary is qualified by a correction sidecar. Original artifacts, scores and telemetry remain unchanged; these corrections were made outside the measured runs.

## Comparison design

| Configuration | Capabilities |
|---|---|
| Baseline | Original statistical skills, Python, direct public APIs, ordinary notes/files and cached source reuse |
| Upgraded | Same skills and source access, plus typed controller, native MCP tools and fingerprint-scoped project memory |

Both used gpt-6-astra with medium reasoning, identical input bytes and source guide, 900-second initial budgets and 600-second fresh-session follow-up budgets. All four sessions completed without timeout. Each arm could reuse its own prior files; the baseline was not forced to reread the conversation or redownload sources. Actual prompts, frozen rubric and protocol are included. Search choices and some exploratory shortlist rules differed despite the common task; these differences are documented in the review. One bundled pilot cannot isolate the effect of MCP, memory or controller, and no replicated statistical comparison of agents was performed.

## Data and analysis

Processed RNA and protein matrices came from [LinkedOmics CPTAC-CCRCC](https://www.linkedomics.org/data_download/CPTAC-CCRCC/), corresponding to [Clark et al., Cell 2019](https://pmc.ncbi.nlm.nih.gov/articles/PMC7331093/). Authoritative published clinical annotations and specimen metadata came through the public CPTAC maintainer index; see [sources](DATA_SOURCES.md).

Starting with 110 tumors, histology/specimen exclusions and the four-assay intersection produced **72 patients with paired tumor/adjacent-normal RNA and protein measurements**. The follow-up restricted those same patients to **37 Stage I/II cases**. This is exploratory paired molecular profiling, not a causal treatment study.

Primary inference used finite paired tumor-minus-normal means, paired t intervals/tests, at least 20 pairs, and BH correction separately per assay. No imputation or extra log transformation was used. Protein and RNA effects remain on their distinct supplied scales. Both arms tested 10,033 proteins (8,219 q<.05) and 19,015 RNA genes. Across 9,475 jointly tested genes, 7,205 had matching directions (76.04%). CA9/NNMT increased in both assays; MTOR abundance decreased, which does not establish kinase activity. VEGFA protein could not be tested. Both selected NDUFA4L2 and MT1H as exploratory candidates.

The fresh-session follow-up applied ≥80% within-cohort completeness and ≥20 pairs, requiring 58 all-stage or 30 early-stage pairs, and recomputed four BH families:

| Cohort | Proteins tested / q<.05 | RNA genes tested / q<.05 |
|---|---:|---:|
| All-stage 72 | 8,054 / 6,838 | 19,015 / 15,118 |
| Stage I/II 37 | 8,087 / 6,436 | 18,915 / 14,077 |

An independent reviewer reconstructed cohorts and checked every exported tested mean/count/p/q and interval in both follow-ups. Same-direction proportions among shared tested genes were 95.83% protein and 95.07% RNA. These overlapping cohorts are not independent validation; significance changes are not interaction tests. Missingness, batch/purity, adjacent-normal biology, selection and interval assumptions remain unresolved.

## What MCP and memory actually did

Upgraded made **13 successful native MCP calls**: two protein annotation calls, three target-evidence calls, two literature searches, two trial searches and four trial-detail calls. UniProt mappings/Reactome cross-references, Open Targets records, publications and ClinicalTrials.gov records were saved with source URLs, dates and hashes. This is annotation and bounded evidence retrieval, not pathway enrichment or proof of therapeutic benefit. Full matrices were downloaded by the host, not MCP. All scientific plots were made in Python.

In the fresh session, memory returned **six fingerprint-matched decisions, 4,462 UTF-8 bytes** (not a token measurement). These covered cohort, scales, missingness, estimator, shortlist and source interpretation. Follow-up code checked the decisions against saved configuration and used them in computation; the original eight memory records remained unchanged and one sensitivity record was appended. Baseline also successfully reused ordinary notes, saved functions and source snapshots. Both preserved original scientific outputs. Structured memory makes decisions easier to inspect, but does not ensure their narrative is correct, as the VEGFA erratum illustrates.

The controller recorded stages and blocked evaluation pending review; it did not prevent exploratory artifact generation or independently validate science. Initial upgraded code had local exclusion/CI constants despite retrieving configuration; follow-up code improved this integration. Changed-decision robustness remains untested.

## Actual token usage

| Configuration | Phase | Total input | Cached input | Uncached input | Output |
|---|---|---:|---:|---:|---:|
| Baseline | Initial | 901,932 | 842,496 | 59,436 | 17,279 |
| Baseline | Follow-up | 504,887 | 435,840 | 69,047 | 11,631 |
| Upgraded | Initial | 1,899,009 | 1,808,128 | 90,881 | 19,602 |
| Upgraded | Follow-up | 690,272 | 616,064 | 74,208 | 13,348 |

Overall upgraded used **28.5% more uncached input** (165,089 vs 128,483) and **14.0% more output** (32,950 vs 28,910). Total accumulated input was 84.1% higher; follow-up uncached input alone was 7.5% higher. Cached input is part of total input, not an additional count. These are actual CLI turn telemetry, not context-window occupancy or billed cost. Reasoning output is a subset of output. Setup, parent orchestration, reviewer and post-review correction usage are excluded.

Initial durations were 10.0/12.4 minutes baseline/upgraded; follow-ups 6.3/7.8. Latency and usage include troubleshooting: an experimenter-provided font cache was initially empty for both arms, and the upgraded quickstart initially used a wrong memory keyword. The upgraded agent inspected the API and fixed it. These are setup faults, not intrinsic memory costs. Both also recovered from unavailable openpyxl using supplied CSV/standard-library reading. No estimated troubleshooting tokens were subtracted, and no selective reruns were performed. See [setup corrections](setup_corrections.json).

## Visual and scientific quality

The frozen initial rubric scored baseline 20/24 and upgraded 19/24; these unblinded single-reviewer scores are descriptive, not evidence of a winner. Upgraded initially included more explicit shortlist uncertainty and useful negative CA9 therapeutic evidence; baseline had broader sensitivity checks and some additional trial context. Both follow-ups included paired uncertainty plots. The upgraded follow-up required the count correction above. Neither offered uniformly superior visualization; density legends and some label placement need refinement.

The direct API trial queries were broader than the MCP intervention-field queries. More hits cannot be attributed to the protocol. Both retained complementary evidence gaps. Registry phase/status and target associations do not prove efficacy; diagnostic imaging and treatment trials are kept distinct. Full recruitment/provenance audits and independent biological validation remain future work.

## Reproduce and inspect

`prepare_inputs.py INPUT_DIRECTORY` downloads the public source files, extracts clinical annotations (requires openpyxl) and verifies all nine exact hashes against `INPUT_MANIFEST.json`. The clinical extraction was reproduced and matched the frozen fingerprint. Upstream files may change; the script fails rather than silently accepting new bytes.

The arm folders contain the actual scripts, aggregate tables, reports, versions and provenance indexes. They are **audit artifacts, not a turnkey portable package**: scripts retain session paths, raw source snapshots are not bundled publicly, and upgraded reproduction needs the matching runtime and memory database. Adjust paths only in a separate reproduction directory. `launch.py` records the actual model/session setup; prompts and source guides record the common contract. Live API responses and future model runs need not reproduce byte-for-byte.

The complete local archive is `outputs/ccrcc-agent-pilot` (Git-ignored), including input matrices, raw source responses, model logs and the frozen memory database. Public exports omit raw matrices and provider response bodies; aggregate gene tables and public cohort identifiers remain. Raw source hashes/indexes remain auditable against the local archive. Generated preview screenshots are not published.

For continuing the upgraded study, first apply/read `post_review/memory_correction.json`; do not reuse the unqualified frozen VEGFA summary. Preserve original benchmark files. The next useful engineering steps are a compact resume helper, a single validated configuration driving all computation, source-query comparability and figure labels generated from result tables. Test these on repeated cases before claiming efficiency gains.
