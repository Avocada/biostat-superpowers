# Day-1 RHC and 30-day mortality

Day-1 RHC was associated with higher recorded 30-day mortality: 830/2,184 (38.0%) versus 1,088/3,551 (30.6%). The crude risk difference was 7.36 (95% CI 4.83 to 9.90) percentage points; the risk ratio was 1.24 (95% CI 1.15 to 1.33).

**Interpretation:** higher recorded mortality among RHC recipients, not proof that RHC caused harm.

- **Population:** all 5,735 supplied patients; 2,184 RHC, 3,551 No RHC; no exclusions, no missing treatment/outcome labels, unique IDs. Original screening denominator unavailable.
- **Exploratory legacy IPTW:** weighted risks 36.6% versus 31.6%; RD 5.00 (95% CI 2.20 to 8.40) percentage points; RR 1.16 (95% CI 1.07 to 1.28). 120 full-pipeline patient bootstrap replicates, seed 240924. Intervals reflect sampling under the single-imputation procedure, not uncertainty from bias or a valid MI model.
- **Balance/overlap:** 72 encoded terms; mean absolute SMD 0.140 → 0.018; max after 0.070; 0 terms above 0.10. 85 propensity scores clipped; no patients trimmed. Effective N: RHC 1140, No RHC 2132.

## Why causal interpretation is unresolved

1. **Timing:** study day 1 means first qualifying SUPPORT day; ICU first-24-hour wording is not proven equivalent. No within-day treatment/covariate ordering. Physiology, DNR and prognosis cannot all be certified pretreatment; immortal-time, reverse-causation and post-treatment adjustment risks remain.
2. **Missingness:** cat2 4,535/5,735; adld3p 4,296/5,735; urin1 3,028/5,735. Structural blanks are unconfirmed. Legacy categorical coding folds blanks into reference; median fill is not multiple imputation. Encoding/omission sensitivity does not validate MAR or MNAR.
3. **Identification:** no justified sufficient adjustment set; confounding by indication and unmeasured clinical judgment remain. Positivity, consistency, no interference and model adequacy are not established. Historical five-hospital data do not establish current clinical effects.
4. **Review:** analyst self-audit only; independent review pending and no human scientific approval. Site clustering cannot be addressed from these fields.

## Legacy corrections

The preserved script was not executed unchanged: its estimator was transcribed to use the supplied bytes offline. Clipping is not overlap trimming. Its logistic treatment coefficient is a conditional OR, not g-computation (OR 1.37). Balance now uses a fixed unweighted SD and all-term diagnostics. Point E-value 1.59 is an assumption-dependent confounding benchmark, not causal validation. Alternative clipping and missingness specifications are exploratory point estimates, not MNAR analyses. No new clinical value corrections were made.

## Added components and artifacts

- **Controller:** actual route/advance/settle transitions in workflow-transitions.json. Causal branch blocked at preparation; inferential branch blocked at independent evaluation. Both stop at the configured one-block no-progress threshold; neither is marked successful.
- **MemoryStore:** project-memory.sqlite3 stores four analyst-attributed, fingerprint-bound records. Retrieved scope/timing constrained labeling, profile informed missingness handling, and source distinguished published matching from legacy IPTW. Retrieval saved in memory-retrieval.txt; no human approval inferred.
- **Native MCP:** imported/profiled the identical CSV, rendered a profiled age histogram, retrieved PubMed abstract and citations. Raw responses, chart specification, figures, hashes, timestamps and provenance remain in mcp_artifacts/. Tool outputs are exploratory, not approved evidence.
- **Local Python:** analysis.py computes estimates, diagnostics, 120 bootstrap replicates and figures; build_report.py produces a self-contained offline report.html. No package installation, external model APIs, Jev, or delegation.

View **report.html** for figures, interactive diagnostic panels, captions and fuller limitations. See **results.json**, **tables/**, **figures/**, **analysis-contract.json**, **decision-log.md**, and **artifact-manifest.json** for audit details. All images are embedded; no CDN dependency.

Reproduce offline:

```sh
/tmp/biostat-rhc-analysis-env/bin/python analysis.py
/tmp/biostat-rhc-analysis-env/bin/python build_report.py
```

Requires the supplied environment and read-only runtime at /Users/amiee/Projects_code/biostat-superpowers. Input SHA-256: `811bad3c113c26acc64c00ed149993b09dd320cf2540b750738f5656233d2ec6`. Software versions: requirements-observed.txt.

Source: Connors AF Jr et al. The effectiveness of right heart catheterization in the initial care of critically ill patients. SUPPORT Investigators. JAMA. 1996;276:889–897. PMID 8782638. DOI 10.1001/jama.276.11.889. MCP-retrieved abstract confirms setting/design; the published matching OR is not this IPTW estimator. Dictionary and CSV were supplied from https://hbiostat.org/data/repo/rhc.html and https://hbiostat.org/data/repo/rhc.csv. Source retrieval cached 2026-09-24.
