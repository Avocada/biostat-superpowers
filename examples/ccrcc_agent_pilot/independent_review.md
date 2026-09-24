# Independent initial-artifact evaluation

Reviewed 2026-09-24 against the protocol frozen at `/tmp/ccrcc_review_protocol.md`. Arm identities were visible; this was not blinded. Sources were the immutable `baseline_initial_snapshot` and `upgraded_initial_snapshot` directories. I inspected both analysis scripts, full result tables, Markdown reports, all eight actual PNGs, saved source responses and provenance, upgraded memory retrieval and controller records, and setup-correction notes. I did not modify either arm or rerun its analysis script. Independent calculations below are verification of exported results, not a new scientific analysis. Follow-up performance is pending and unscored.

## Main judgment

Both initial analyses are **conditionally ready for the explicitly limited exploratory tissue-association use**. Neither demonstrates causal regulation, a validated biomarker, or drug efficacy. No critical defect was identified in the reported initial numerical results. Both recover the same core science and avoid the major pairing, scale, significance-difference, and VEGFA errors. The upgraded arm adds structured provenance, a useful uncertainty figure, and negative CA9 clinical context; the baseline adds broader sensitivity checks and literature context. This run does not establish overall superiority or a causal benefit from the upgraded architecture.

A stronger mechanistic/publication claim would need revision: abundance-dependent missingness, common-assay selection, batch/purity/cell-composition confounding, and independent validation remain unresolved. A caveat does not establish robustness to these problems, but the caveats appropriately constrain the present estimand.

## Frozen rubric scores

Scores use the frozen 0–3 anchors. Domain 8 is provisional because the fresh-agent follow-up has not been reviewed. Totals are descriptive, not efficacy metrics; differences of one point are reviewer judgments rather than estimated effects.

| Domain | Baseline | Upgraded | Evidence and reason |
|---|---:|---:|---|
| Scope/cohort | 3 | 3 | Both reconcile 110 downloaded tumors with seven histology exclusions and separate contaminated normal exclusion; common cohort explicit |
| Pairing/scale | 3 | 3 | Exact case-ID matching, unique keys, within-case differences, distinct processed scales, no double log |
| Inference/missingness | 3 | 3 | Gene-wise n/status, explicit n≥20, full BH families, correct t intervals and no protein inference for VEGFA |
| Discordance/integration | 3 | 3 | Descriptive signs/correlation, common-finite sensitivity, no claim that differing significance tests a layer difference |
| Robustness | 2 | 1 | Baseline includes layer-specific cohort sensitivity, leave-one-out and bootstrap; upgraded initial includes same-finite comparison and leave-one-out only; neither varies coverage thresholds or resolves MNAR/batch |
| Evidence/pathways | 2 | 2 | Both auditable and bounded; complementary gaps, no enrichment claim; neither systematic nor full-text independence audit |
| Visual communication | 2 | 2 | Upgraded stronger shortlist uncertainty and highlights; baseline clearer low-coverage distribution; both omit an RNA-wide differential plot and have small labeling weaknesses |
| Reproducibility/follow-up | 2 provisional | 2 provisional | Both have code, inputs and decisions; upgraded structured state is auditable but has portability/enforcement limitations; follow-up unreviewed |
| **Provisional total** | **20/24** | **19/24** | **Do not interpret a one-point difference as a winner** |

## Independent numerical and cohort verification

All nine input hashes matched each arm's manifest; the two manifests were byte-identical. Independently derived histology exclusions from clinical_annotation.csv are C3L-00359, C3N-00313, C3N-00435, C3N-00492, C3N-00832, C3N-01175 and C3N-01180. The workbook's shared strings explicitly record removal of NAT CPT0012090003 for tumor contamination; supplied metadata and both code paths map this to C3N-00314 normal. Tumor inventory retains this case, while paired analysis necessarily omits it. Four-way intersection after exclusions gives **72 distinct cases**. Protein has 80 eligible tissue pairs before the four-way restriction; RNA has 72. The 103 is eligible tumors, not the paired sample size.

I reconstructed tumor-minus-normal differences from the supplied matrices, used independent SciPy one-sample tests of paired differences and SciPy BH adjustment, and compared every tested gene's n, mean, p and q against both exports. All comparisons passed (p/q relative tolerance 1e-8; means absolute tolerance 1e-12). Full exported t confidence bounds also agreed with their documented formula and between arms. Results:

- Protein: **10,033 tested; 8,219 q<0.05**.
- RNA: **19,015 tested; 15,118 q<0.05**.
- **9,475** genes tested in both; **7,205** have matching signs; **1,087** have opposite estimated signs and q<0.05 in both.
- VEGFA protein: **n=1**, descriptive mean **1.06849555**, no valid inferential p/q/interval; RNA: **n=72**, mean **3.01434399**. Both reports handle this correctly.

I also verified all upgraded MCP manifest file hashes and byte counts. Verification used saved source snapshots; it does not establish external database correctness or re-audit the original laboratory processing.

The baseline's same-finite sensitivity has 9,482 genes because it includes seven constant RNA genes; its main tested-only comparison correctly uses 9,475 and the report explains the difference. Upgraded uses 9,475 tested-in-both genes throughout that sensitivity. These sensitivity percentages therefore should not be compared as evidence of one method improving agreement.

## Scientific findings and required actions

**Medium, both — robustness scope remains limited.** Main code implements a transparent paired t analysis, correct per-layer BH, explicit zero-variance status and nominal intervals. However, n≥20 permits inference using fewer than a third of the common cohort for some proteins. Tissue-level missingness summaries and influence checks do not show that these available-pair effects are unbiased. Before elevating the genome-wide ranking, the analysis owner should compare prespecified alternative coverage thresholds and shortlist/rank stability and inspect batch/purity information if available. Keep present claims about observed pairs.

**Medium, upgraded — less initial sensitivity coverage.** `diagnostics.json` supplies shortlist skew/influence summaries, but no initial 80-pair protein sensitivity or bootstrap interval outputs comparable to baseline's `outputs/protein_layer_cohort_sensitivity.csv` and shortlist fields. Add them only if needed for scientific use; their absence does not invalidate matching 72-pair estimates.

**Low, comparison — shortlist rules are not exactly identical.** Baseline requires an RNA test to be available before ranking nonprespecified proteins; upgraded does not. They happen to select the same NDUFA4L2 and MT1H here. Record this as a design deviation; harmonize in a future controlled experiment, not retroactively in these frozen runs.

**No identified inference violation — discordance.** Both correctly frame sign discordance and Spearman association across genes as descriptive, not a direct cross-assay equality test. Two separate q<0.05 results are not a multiple-testing-controlled test of a regulatory mechanism. Neither report claims otherwise. Different RNA/protein scales, cell composition and processing remain possible explanations.

**No enrichment error.** Neither runs enrichment. UniProt/Reactome annotations are explicitly labeled annotations. Therefore a pathway-background defect is not applicable here; do not reward absence of enrichment as a successful enrichment analysis.

## Evidence review

Baseline source snapshots support the reported 626-patient temsirolimus trial and OS HR 0.73 (0.58–0.92), and the 750-patient sunitinib trial and PFS HR 0.42 (0.32–0.54). These are independent historical clinical contexts, not CPTAC validations and not evidence that tissue abundance predicts benefit. The initially guessed cardiac-trial PMID remains in `mtor_independent.json` but is correctly rejected in the report; the actual temsirolimus abstract is in `mtor_renal.json`. Retaining the failed lookup is legitimate audit history, although more explicit superseded-file labeling would reduce reuse risk. Its ZIRCON reanalysis is correctly described as independent of CPTAC but not independent of ZIRCON.

Upgraded saved ARISER abstract supports 864 participants and null overall DFS/OS contrasts; report estimates match. Including negative CA9 therapeutic evidence usefully prevents one-sided prioritization. The retrieved Kim NNMT abstract specifies new paired RNA sequencing in 14 patients and separate cell-line experiments/TCGA survival analysis; upgraded preserves these component distinctions. However, “separate” human cohort independence remains abstract-supported rather than a full-text recruitment/date audit. Both arms appropriately leave possible CPTAC reuse in the newer NNMT multiomics paper unresolved.

**Medium, both — bounded search coverage.** Baseline lacks the negative ARISER context; upgraded lacks independently retrieved MTOR/VEGF pathway trials and NDUFA4L2 candidate literature. These are complementary coverage gaps, not fabricated evidence. Upgraded explicitly says no such evidence was retrieved rather than claiming none exists. Before using the shortlist for experimental investment, the evidence owner should run a common prespecified search, include negative studies and audit recruitment/provenance for claimed replication. Do not attribute these search-choice differences specifically to MCP or memory.

## Actual PNG inspection

All eight PNGs were readable, with correct direction and assay labels and no obvious clipping of central plotted data. The baseline's log-scaled coverage histogram makes sparse-pair proteins visible; upgraded's linear histogram compresses that information near zero. Upgraded's highlighted protein scatter and q threshold improve interpretation; its separate-assay shortlist CIs provide genuine uncertainty communication and clearly omit VEGFA protein inference. Baseline has no comparable shortlist CI figure. Neither provides an RNA-wide differential display, despite having RNA tables.

Low-priority visual fixes for the reporting owner: label the upgraded density plot color/count meaning (currently no colorbar); label its n=20 vertical coverage threshold; add gene-wise n to shortlisted CI labels; add a legend/q-threshold label to baseline protein colors. Baseline selected-gene text overlaps point clouds slightly. These are usability limitations, not false numerical figures. No browser-rendered HTML screenshot was independently assessed; PNG QA and code/table assessment should not be presented as full browser visual QA.

## Runtime mechanics, kept separate from science

Upgraded `memory_retrieval.json` contains six usable keyed decisions with the input fingerprint, and `analysis.py` retrieves them before estimation. Native MCP response manifests persist URLs, dates, raw bytes, hashes and truncation caveats; the verified artifacts provide tangible provenance. Baseline also persists raw API responses, provenance, ordinary decisions and reproducible code. Thus the observed distinction is more structured handling, not unique ability to obtain external evidence.

Controller audit records design → preparation → missing_data → analysis → evaluation, with evaluation explicitly blocked and no approval. This is a real record of state transitions, but not an independent certification: stage evidence is analyst-supplied text and analysis.py still writes a report/figures after blocking. The report accurately labels independent evaluation pending. Do not describe the controller as technically preventing all report generation or scientifically validating the results.

**Medium runtime limitation — configuration authority/portability.** Upgraded updates config from memory, but case-set construction subtracts local `exclude` rather than `config['exclude_histology']`; confidence intervals use a hardcoded .975 rather than config['ci']. Current values agree, so current numerical results are unaffected. A future memory change could be accepted yet ignored by portions of computation. The runtime owner should route all effective analysis choices through one validated configuration or assert equality, and include a test of changed decisions. Its hardcoded local runtime source path also limits portability; preserve a versioned runtime dependency for reproducibility. This is a code integration limitation, not a generic defect of memory.

Both arms had the parent-supplied empty font-cache setup corrected. Upgraded read an experimenter-authored incorrect max_bytes example, inspected the actual API and corrected it to max_units/count. These are setup overhead, not inherent structured-memory failures. No latency/token winner is declared here; no comparable complete accounting was supplied for this review.

## Handoff

Keep both initial reports as exploratory, caveated artifacts. For subsequent work, prioritize harmonized evidence searches, missingness/coverage sensitivity, runtime configuration authority and an independent cohort validation plan. The follow-up review should test what the new agents actually recover and compute, without treating a fluent memory summary as proof. Both arm authors retain ownership of corrections; this independent review changes no frozen artifact.

# Follow-up addendum — completed runs

Reviewed after `/tmp/ccrcc-study/upgraded_followup_execution.json` existed. Both fresh-agent follow-ups, their analysis code, reports, full exported tables, source indexes, actual four new PNGs and preservation evidence were reviewed. Arm identities remained visible. No arm artifact was edited.

## Follow-up numerical verdict

**Both successfully continued the original paired analysis and produced matching, correct numerical sensitivity results.** I independently reconstructed the stage cohorts from the authoritative clinical annotation: 28 Stage I, 9 Stage II, 23 Stage III and 12 Stage IV; 37 early-stage patients are a subset of the original 72, with no unknown stage. Independent input-based means, counts, SciPy paired-difference tests and BH checks passed for all tested genes in all four families in both arms. All exported confidence bounds also passed formula checks.

| Cohort | Required pairs | Protein tested / q<.05 | RNA tested / q<.05 |
|---|---:|---:|---:|
| Original all-stage 72 | 58 | 8,054 / 6,838 | 19,015 / 15,118 |
| Stage I–II 37 | 30 | 8,087 / 6,436 | 18,915 / 14,077 |

Both use within-cohort ≥80% completeness plus ≥20 pairs, recompute BH over four distinct valid-test families, preserve original finite-pair estimands and correctly caution against interpreting significance differences as stage interaction. The smaller cohort can retain additional proteins under a proportional completeness rule. Both identify the changed families and overlapping-case dependence rather than claiming independent replication. They retain the same NDUFA4L2/MT1H exploratory selection and avoid kinase-activity or drug-efficacy claims.

**Medium reporting error, upgraded — early-stage VEGFA count was carried incorrectly into prose and the figure.** Actual matrix values and both arms' exported tables establish VEGFA protein **n=1 all-stage and n=0 early-stage**. The completed upgraded `FOLLOWUP.md` says “one finite pair in each cohort”; `followup_figures/shortlist_comparison.png` explicitly labels “n=1 / 1,” and the corresponding label is hardcoded in `followup_analysis.py`. Its table correctly says 0 early-stage and no test is computed. This does not reverse the untestable conclusion, but is a concrete incorrect scientific fact in the user-facing artifact and should be corrected before distribution. Generate the prose/annotation from result rows, not a carried-over initial fact. The added sensitivity memory summary also mentions VEGFA n=1 without cohort qualification; qualify that decision as 1/0 to avoid perpetuating the ambiguity. Baseline reports 1/0 correctly. The observed association with a remembered initial n=1 is not proof that memory caused the error.

Top-list comparison metrics differ by implementation: baseline reports top-50 overlap from each cohort's own family, while upgraded reports top-100 from the shared tested universe. Both disclose their definitions; their overlap values are not head-to-head metrics of workflow quality. Neither has established stage invariance or interval coverage. Baseline explicitly flags pronounced early-stage RNA skew for CA9/VEGFA/NDUFA4L2; upgraded saves influence/skew summaries but provides less specific narrative warning. Direction stability after one deletion does not validate t-based coverage in either arm.

## Actual follow-up visual assessment

Both new shortlist plots communicate separate assay scales, paired intervals, overlapping cohorts and VEGFA ineligibility. Baseline marks initial data-selected candidates with asterisks and a selection-adjustment caveat in the image itself. Upgraded retains readable grouped points but has the erroneous VEGFA count noted above. Both effect-comparison plots correctly label overlap-induced/descriptive agreement. Some RNA labels near CA9/NDUFA4L2 overlap in both. Upgraded still omits a density colorbar; both comparison plots could state assay units directly on the axes rather than relying on companion text. These last issues are low priority. The numerical VEGFA label is the material figure correction. No full browser screenshot inspection was performed for either HTML report.

## Registry evidence and scope

Both preserve snapshot dates/status verification and distinguish diagnostic imaging from treatment, planned outcomes/phase/status from demonstrated benefit, and advanced-disease combination studies from applicability to early-stage tissue samples. Reuse of ZIRCON/ARISER is not presented as additional independent replication. No new efficacy effect estimate was fabricated.

Searches are **not identical**. Baseline makes two broader direct API searches (CA9 OR girentuximab, and NNMT OR its full name), retrieves 49 and 1 records, and reviews six. It correctly identifies the NNMT hit as a hydroxychloroquine study measuring NNMT as a secondary biomarker, not an NNMT-targeted treatment; termination for recruitment barriers is not called efficacy failure. It additionally reviews a phase 3 radioligand study not discussed by upgraded.

Upgraded uses two narrower native MCP intervention-field searches, then four detail calls. Its literal NNMT search returns zero, properly described as a bounded negative query rather than absence of relevant trials. The girentuximab source unusually contains both totalCount=20 and a next-page token; the report preserves and discloses this inconsistency instead of asserting completeness. Its reuse of the original ARISER null-result publication adds useful negative therapeutic context beyond baseline's current registry description. All current upgraded MCP artifact file hashes were verified. These are complementary evidence choices and different query scopes; greater hit count or additional detail calls cannot establish connector superiority. Native MCP made provenance more standardized, but the direct API arm also preserved traceable source evidence.

## Actual reuse and preservation

Baseline recovers original decisions, input identities, shortlist and limitations from ordinary files, extracts the original estimator/BH function bodies without executing the original analysis, and reuses cached annotations/literature. It adds the requested sensitivity and trial context without rerunning the original report. Upgraded retrieves six original fingerprint-matched decisions (4,462 UTF-8 bytes, **not tokens**), checks them against saved configuration, reconstructs the original cohort, and uses retrieved exclusion/CI fields in the new computation. The initial concern about local exclusion/CI constants is addressed in this new follow-up implementation; the original frozen code is appropriately unchanged. Some intended fixed values (80%, ≥20, q<.05) remain literal but agree with this request and validated configuration; no changed-decision robustness experiment was conducted.

Read-only comparison with the initial snapshots found **no changed baseline original files** (excluding font cache). Upgraded changes are exactly the continuation note, retrieval log and memory database: original `FOLLOWUP.md` is copied byte-for-byte to `followup_initial_notes.md`; original reports, results, tables, input data, code, source snapshots and figures remain unchanged. SQLite comparison verifies all eight original memory rows unchanged and one new sensitivity row appended, with analyst attribution and no fabricated independent approval. This is successful structured continuation and an audit trail. Baseline's ordinary-note continuation is also successful. Neither the mere presence of memory nor the controller's pending state proves correctness; upgraded's persisted narrative still contains the VEGFA limitation described above.

## What benefit is demonstrated?

Demonstrated upgraded capabilities: usable fingerprint-scoped retrieval, configuration agreement checks, structured source manifests, explicit controller state and non-destructive decision append. These make state/provenance easier to inspect. **No superiority in numerical science or substantive continuation success is demonstrated:** both obtain identical valid sensitivity estimates, preserve original scientific outputs and reuse prior sources. Baseline has broader trial search coverage and correctly reports the early-stage VEGFA count; upgraded carries useful ARISER negative context and stronger structured runtime records. The current trial differences depend on query choices and inherited evidence, not an isolated architecture intervention.

Initial scores remain a record of the initial artifacts and are not retroactively changed. Follow-up evidence supports successful continuation for both; upgraded requires a targeted prose/figure/memory-summary correction. Both remain conditionally usable for bounded exploratory research, with the existing MNAR, selection, batch/purity and independent-validation limitations. Do not claim token savings, latency gains or general architectural benefit from this artifact assessment; telemetry and repeated controlled cases are needed for those questions.
