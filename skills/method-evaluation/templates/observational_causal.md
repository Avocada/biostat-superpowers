# Observational and Causal Method Evaluation Template

Use for observational comparisons, adjustment strategies, propensity scores, matching, weighting, difference-in-differences, instrumental variables, regression discontinuity, and causal language review.

## Specify

- Exposure/treatment, outcome, population, time zero, follow-up window, causal contrast, and target estimand.
- Confounders, mediators, colliders, instruments, eligibility criteria, and censoring.
- Identification strategy and whether assumptions are plausible in the domain.

## Assumptions

- Exchangeability or no unmeasured confounding for adjustment-based methods.
- Positivity/overlap across treatment groups.
- Correct temporal ordering: confounders before exposure, outcome after exposure.
- No conditioning on mediators or colliders unless intentionally estimating a controlled/direct effect.
- Design-specific assumptions for DiD, IV, or RD.

## Diagnostics

- Covariate balance before and after adjustment, matching, or weighting.
- Overlap and extreme weights.
- Outcome and exposure timing checks.
- Negative controls, placebo outcomes, or pre-trend checks when applicable.
- Attrition and censoring patterns.

## Stress Tests

- Alternative adjustment sets based on defensible causal diagrams.
- Propensity model specification, trimming, caliper, and weight truncation sensitivity.
- Unmeasured-confounding sensitivity analysis.
- Negative-control or placebo checks.
- Alternative time-zero, eligibility, and follow-up definitions.

## Compare

- Unadjusted descriptive comparison as context, not causal evidence.
- Regression adjustment, matching, weighting, and doubly robust variants when assumptions align.
- Compare balance, overlap, and estimand changes, not only p-values.

## Improve

- Draw or describe the causal structure before modeling.
- Tighten eligibility and time-zero definitions.
- Improve overlap through restriction or trimming with estimand implications stated.
- Replace causal claims with associational language when identification is weak.
