# Continuation notes

Completed only the requested nested stage sensitivity and two-concept registry search. No other arms read; no delegation, installs, runtime, MCP or SQLite. Independent review remains pending.

Input fingerprint verified: ff08dba38c4df7e1f899b4ebecb713f6aa49d24cb074d9f9c30478a1e1571f0f. All 80 pre-existing tracked files remain unchanged; see followup_outputs/original_hashes.json and validation.json. Original report/results/figures are untouched.

Original primary cross-modal cohort 72; exact authoritative Stage I/II subset 37 (28/9). Completeness thresholds 58 and 30 finite pairs. Tested protein 8054/8087, RNA 19015/18915 (all/early). Each layer/cohort has its own BH family. Exact original paired mean, sample-SD t test/CI, scales, no-imputation and zero-variance handling retained. analyze/bh extracted by AST to avoid executing initial analysis. All-stage means checked against initial saved results; q values necessarily change with protein family.

Original shortlist direction persists; reselected exploratory genes remain NDUFA4L2 and MT1H. VEGFA protein n=1/0 is untestable. Direction agreement common genes: protein 95.8%, RNA 95.1%. Overlap induces concordance; no interaction, independence, equivalence or robustness claim. RNA shortlist skewness is substantial; t intervals are model-based and not selection-adjusted.

Two new ClinicalTrials API requests, 2026-09-24: CA9/girentuximab kidney query (49 hits) and NNMT/full verified protein name kidney query (1 hit), no pagination needed. Six illustrative records reviewed; other hits archived, not asserted target-directed. NNMT hit NCT01144169 measures NNMT among serum biomarkers; hydroxychloroquine is not verified NNMT-targeting. CA9 examples separate diagnostic ZIRCON from treatment trials; no efficacy extracted. All statuses/dates and raw bytes/hashes saved. No new literature/annotation requests; prior evidence unchanged and cohort-overlap limitations retained.

Rebuild in order with /tmp/biostat-rhc-analysis-env/bin/python: followup_analysis.py; followup_trials.py; followup_report.py. Trial script reuses its snapshots, without silent refresh. Reports: followup.html (embedded PNGs, offline), FOLLOWUP.md. Machine data: followup_results.json, context_sources.json. Aggregate tables/figures/checks: followup_outputs/. Both actual new figures visually inspected. Follow-up report builder performs independent scipy numerical checks and original-file hash checks.

Unresolved: independent review; selection/MNAR; raw processing/batch and cell composition; t-interval finite-sample coverage; full-text cohort independence; registry currency and trial outcomes. No scientific approval or causal/clinical conclusion.
