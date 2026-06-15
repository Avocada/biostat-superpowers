# Reporting Guidelines and Table 1

Match the guideline to the design, capture its required elements, and report effects honestly. The
EQUATOR Network catalogs these; the common ones for biomedical research are below.

## Which guideline

| Design | Guideline | A few elements reviewers check |
|---|---|---|
| Randomized trial | **CONSORT** | flow diagram, randomization & allocation concealment, blinding, pre-specified primary outcome, ITT, harms |
| Cohort / case-control / cross-sectional | **STROBE** | eligibility & setting, variables/sources, bias handling, participant flow, confounding control |
| Prediction model (development/validation) | **TRIPOD** | predictors, outcome, sample size/EPV, model building, calibration & discrimination, validation |
| Systematic review / meta-analysis | **PRISMA** | search, selection flow, risk-of-bias, synthesis, heterogeneity |
| Diagnostic accuracy | **STARD** | reference standard, flow, 2×2 results, sensitivity/specificity with CIs |
| Trial protocol | **SPIRIT** | estimand, schedule, analysis plan, monitoring |

Pick it at design time (`study-design-and-power`) so the needed elements are captured prospectively.

## Participant flow

- **CONSORT flow (RCT):** assessed → randomized → allocated (received/did not) → lost to follow-up
  → analyzed, per arm, with numbers and reasons.
- **STROBE cascade (observational):** source population → eligible → included → analyzed, with the
  exclusion reason and count at each step. Must match the cohort attrition table from
  `data-understanding-preprocessing`.

## Table 1 — baseline characteristics

Summarize the sample (overall and by arm/exposure):

- Continuous: mean ± SD if roughly symmetric, else median [IQR]. Report n missing.
- Categorical: n (%).
- **RCT: do NOT report p-values comparing arms at baseline** — randomization makes a "significant"
  baseline difference a chance event by definition. If balance matters, report **standardized mean
  differences** (|SMD| > 0.1 flags imbalance), which is also how you check propensity-score balance
  in `causal-inference`.
- Observational: a by-group comparison can be descriptive, but it is not the analysis.

```r
# R — gtsummary (publication-ready) or tableone
library(gtsummary)
tbl_summary(dat, by = arm, missing = "ifany",
            statistic = list(all_continuous() ~ "{mean} ({sd})",
                             all_categorical() ~ "{n} ({p}%)")) |>
  add_overall()                       # add_difference()/add_p() ONLY when appropriate (not RCT baseline)
```
```python
# Python — tableone
from tableone import TableOne
TableOne(df, columns=cols, categorical=cat_cols, groupby="arm", pval=False)  # pval=False for RCT
```

## Reporting effects

- Lead with the **effect size and 95% CI** on a named, interpretable scale: mean difference, risk
  difference, risk ratio, odds ratio, hazard ratio. The p-value is supporting context, not the
  result.
- State the **estimand and model** producing the number ("adjusted HR from a Cox model, covariates
  …").
- Give **absolute and relative** effects where possible: a risk ratio of 2.0 means very different
  things at 1% vs 30% baseline risk. Report the baseline/control risk alongside the ratio.
- Use the **correct label**: an odds ratio is not a risk ratio; a hazard ratio is not a risk ratio.
- Number of decimal places should reflect precision, not false certainty.
- Pre-specified vs exploratory results must be distinguishable, with the multiplicity approach
  stated.

## Figures

- Survival: Kaplan–Meier with a **numbers-at-risk** table; censoring marks.
- Subgroups / meta-analysis: **forest plot** with point estimates, CIs, and (for meta-analysis)
  heterogeneity (I²).
- Prediction models: **calibration plot** (observed vs predicted) plus discrimination (ROC).
- Effects: plot estimates with CIs; prefer over bar-charts-of-means that hide spread.
