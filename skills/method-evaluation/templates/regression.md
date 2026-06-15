# Regression Method Evaluation Template

Use for linear, logistic, count, ordinal, survival, mixed, clustered, robust, penalized, and spline regression.

## Specify

- Outcome scale: continuous, binary, count/rate, ordinal, nominal, time-to-event.
- Estimand: mean difference, slope, odds ratio, rate ratio, hazard ratio, conditional effect, population-average effect, prediction error.
- Unit of analysis, clustering, repeated measures, weights, offsets, exposure, censoring, and sampling design.
- Primary predictors, adjustment covariates, interactions, nonlinear terms, and reference levels.

## Assumptions

- Correct outcome distribution or link for the target.
- Independence or correctly modeled clustering/repeated measures.
- Functional form for continuous predictors.
- Adequate events, cells, or information for parameters.
- No severe collinearity or separation.
- Missing-data policy supports the target population.
- For survival: censoring definition, proportional hazards if Cox is used.
- For ordinal: order and proportional-odds assumptions if used.

## Diagnostics

- Sample size used, exclusions, event counts, cluster counts, and sparse cells.
- Residuals, fitted values, influence, leverage, and collinearity for linear models.
- Separation, calibration, sparse levels, and influential observations for logistic models.
- Overdispersion, zero excess, offset validity, and mean-variance relationship for count models.
- Proportional hazards or proportional odds checks when relevant.
- Convergence warnings and singular fits for mixed models.

## Stress Tests

- Complete-case versus alternative missing-data policy.
- Alternative functional forms: transformations, splines, interactions, or simpler terms.
- Excluding influential observations or clusters.
- Robust, heteroskedasticity-consistent, or cluster-robust standard errors.
- Alternative count model for overdispersion or excess zeros.
- Alternative survival specification for non-proportional hazards.
- Bootstrap confidence intervals when parametric uncertainty is fragile.

## Compare

- Null or intercept-only model.
- Prespecified simple regression baseline.
- Nested models using likelihood-ratio logic only when fit on compatible rows.
- AIC/BIC for compatible likelihood models.
- Cross-validation for prediction-oriented regression.

## Improve

- Respecify the mean/link structure.
- Add splines or interactions only when motivated by design or diagnostics.
- Use robust methods for heavy tails or influential points.
- Use mixed models, GEE, or cluster-robust inference for clustered data.
- Reduce model complexity when sample size or events are limited.
