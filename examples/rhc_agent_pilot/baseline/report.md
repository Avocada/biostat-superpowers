# RHC: association and limits

Day-1 RHC was associated with higher recorded 30-day mortality: 38.0% versus 30.6%, an observed difference of 7.36 percentage points (95% CI 4.83 to 9.90). This comparison does not establish that RHC caused the difference.

- RHC: 830/2184 deaths; No RHC: 1088/3551 deaths. No exclusions; all 5,735 supplied patients retained. Upstream eligibility flow is unavailable.
- Observed RR: **1.24 (1.15 to 1.33)**; RD: **7.36 (4.83 to 9.90) percentage points**, with 95% independent-binomial approximate confidence intervals.
- Legacy weighted risks: 36.56% vs 31.56%; RD **5.00 (2.36 to 8.03) percentage points**; RR **1.16 (1.07 to 1.27)**. The 95% percentile intervals use 80 patient bootstrap replicates, refitting the legacy pipeline. They do not resolve missing-data, timing or identification uncertainty.
- 85 scores clipped at 0.02/0.98; no patients trimmed. Effective sample sizes: RHC 1140, No RHC 2132. Maximum weighted absolute SMD 0.070; 0 encoded terms above 0.10.

## What prevents a causal interpretation

Eleven patients coded as 30-day survivors have last-contact dates before day 30, so outcome ascertainment needs clarification. Day-1 exposure and covariates have unresolved within-day ordering. Eligibility, early deaths and follow-up must be aligned before specifying a target trial; the absence of t3d30 below 2 does not resolve survivor selection. Acute physiology, DNR and prognosis measurements may be downstream of RHC. Clinical indication and judgment can confound the association. No sufficient adjustment set is established.

cat2 (79.1%), ADL (74.9%) and urine output (52.8%) have substantial missingness. Legacy reference-level encoding and median imputation are not valid substitutes for an explicit missingness model. Bootstrap uncertainty is conditional on that procedure, not MI-pooled inference. Missing-category/indicator and clipping sensitivities are exploratory point estimates; no MAR or MNAR mechanism is confirmed. Cat2 may be structurally absent, requiring source clarification.

The legacy logistic treatment coefficient is a conditional OR, not g-computed marginal risk; it is not reproduced. Mean SMD alone hides imbalance. Clipping is not trimming. The point E-value (1.59) cannot repair timing, selection or missingness. Causal validity also requires consistency, adequate measurement, appropriate models and positivity—not exchangeability alone. All results concern this historical supplied cohort.

**Causal readiness: not_ready.** This is a completed descriptive audit with a qualified computational reproduction, not a completed causal analysis. Independent review is pending; no human scientific approval has been given. Next: verify timing/ascertainment and cat2 meaning, define a clinical DAG and target trial, then develop justified MI and MNAR analyses. No work was delegated.

## Artifacts and reproduction

Open [report.html](report.html) for the self-contained report, embedded figures, interactive diagnostic selector, detailed critique and Table 1. Sources remain local in input/; supplied source attribution identifies Connors et al., JAMA 1996, 276:889–897 (PMID 8782638). The original article was not independently verified here.

```sh
/tmp/biostat-rhc-analysis-env/bin/python analysis.py
/tmp/biostat-rhc-analysis-env/bin/python build_report.py
```

Machine results: [results.json](results.json). Supporting files: balance.csv, missingness.csv, variable_audit.csv, table1.csv, figures/ and decision_log.md. Input SHA256: `811bad3c113c26acc64c00ed149993b09dd320cf2540b750738f5656233d2ec6`. Software versions and seed are in results.json. No network, package installation, external API or remote CDN is required.
