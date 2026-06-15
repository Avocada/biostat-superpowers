# Model Diagnostics and Reporting

Use this reference after fitting a regression model. The goal is to report what was fit, how much data was used, whether assumptions look acceptable, and how to interpret coefficients without overclaiming.

## 1. Universal Reporting Checklist

For every model report:

- Research question and outcome.
- Model family and link function.
- Dataset used and number of rows excluded.
- Missing-data policy.
- Outcome sample size; event count for binary/survival outcomes.
- Predictors and covariates.
- Reference levels for categorical variables.
- Main estimates with confidence intervals.
- Diagnostics and any assumption violations.
- Sensitivity checks if choices could affect conclusions.

## 2. Coefficient Interpretation

Match interpretation to model:

- Linear regression: estimated mean difference or slope on the outcome scale.
- Logistic regression: log-odds on coefficient scale; odds ratio after exponentiation.
- Poisson/negative-binomial: log rate/count ratio on coefficient scale; incidence-rate ratio after exponentiation.
- Cox regression: log hazard ratio on coefficient scale; hazard ratio after exponentiation.
- Mixed models: conditional effects subject to random-effects structure.

Do not use causal language unless study design and adjustment strategy support causal interpretation.

## 3. Confidence Intervals

Prefer confidence intervals alongside point estimates. Use transformed intervals when reporting transformed estimates:

```r
est <- stats::coef(fit)
ci <- stats::confint(fit)

or_tbl <- data.frame(
  term = names(est),
  OR = exp(est),
  CI_low = exp(ci[, 1]),
  CI_high = exp(ci[, 2])
)
```

If profile likelihood intervals are slow or fail for a GLM, state the fallback and use Wald intervals only with caution:

```r
se <- sqrt(diag(stats::vcov(fit)))
wald_ci <- cbind(
  stats::coef(fit) - 1.96 * se,
  stats::coef(fit) + 1.96 * se
)
```

## 4. Linear Model Diagnostics

Minimum checks:

- Residuals versus fitted values for nonlinearity and heteroskedasticity.
- Q-Q plot for residual distribution.
- Scale-location plot when variance concerns matter.
- Cook's distance or leverage for influential observations.
- Collinearity for related predictors.

```r
png("figures/lm_residuals_fitted.png")
plot(fit_lm, which = 1)
dev.off()

png("figures/lm_qq.png")
plot(fit_lm, which = 2)
dev.off()

cooks <- stats::cooks.distance(fit_lm)
influential <- which(cooks > 4 / length(cooks))
```

Report whether diagnostics support the model or motivate sensitivity analyses.

## 5. Logistic Model Diagnostics

Minimum checks:

- Event counts by key predictors.
- Sparse levels or separation.
- Calibration if predicted probabilities are important.
- Discrimination such as AUC only for prediction-oriented tasks.
- Influential observations when sample size is small or estimates are unstable.

Flag warnings such as fitted probabilities numerically 0 or 1. If separation is likely, consider penalized/Firth logistic regression if available, collapse sparse levels when justified, or report that the model is not stable.

## 6. Count Model Diagnostics

Minimum checks:

- Outcome is nonnegative integer.
- Mean-variance relationship.
- Overdispersion statistic.
- Excess zeros and plausible zero-generating process.
- Offset validity for rate models.

```r
dispersion <- sum(stats::residuals(fit_pois, type = "pearson")^2) / stats::df.residual(fit_pois)
```

If overdispersion is substantial, do not rely on naive Poisson standard errors.

## 7. Survival Model Diagnostics

Minimum checks:

- Event and censoring coding.
- Number of events per predictor.
- Proportional hazards assumption.
- Influential observations if estimates are unstable.

```r
ph <- survival::cox.zph(fit_cox)
print(ph)
```

If proportional hazards is violated, consider stratification, time-varying effects, or alternative survival models.

## 8. Mixed Model Diagnostics

Minimum checks:

- Number of clusters and cluster-size distribution.
- Random-effects structure justified by design.
- Convergence warnings.
- Singular fit warnings.
- Residual checks for linear mixed models.

Do not suppress convergence warnings. Report them and simplify or respecify the model if needed.

## 9. Sensitivity Analysis

Use sensitivity checks when conclusions could depend on a modeling choice:

- Complete-case versus alternative missing-data handling.
- Different factor reference levels.
- Excluding influential observations.
- Adding/removing prespecified covariates.
- Alternative outcome transformation.
- Robust or cluster-adjusted standard errors.
- Alternative count model when overdispersion is present.

Label sensitivity models clearly and keep the primary model unchanged unless the user decides otherwise.

## 10. Model Tables

Create tables that are easy to reuse:

```r
coef_mat <- summary(fit)$coefficients
coef_tbl <- data.frame(
  term = rownames(coef_mat),
  estimate = coef_mat[, 1],
  std_error = coef_mat[, 2],
  statistic = coef_mat[, 3],
  p_value = coef_mat[, 4],
  row.names = NULL
)
```

For transformed GLM/Cox estimates:

```r
ci <- stats::confint(fit)
coef_tbl$exp_estimate <- exp(coef_tbl$estimate)
coef_tbl$exp_ci_low <- exp(ci[, 1])
coef_tbl$exp_ci_high <- exp(ci[, 2])
```

Save as CSV and keep a text summary:

```r
utils::write.csv(coef_tbl, "results/model_coefficients.csv", row.names = FALSE)
writeLines(capture.output(summary(fit)), "results/model_summary.txt")
```

## 11. Interpretation Template

Use concise, model-aware language:

```text
We fit a [model family] with [outcome] as the outcome and [main predictor] as the primary predictor, adjusted for [covariates]. The model used [n] observations after excluding [m] rows due to [missing-data rule]. Compared with [reference], [term] was associated with [estimate and CI] on the [scale]. Diagnostics showed [key diagnostic result]. These results are associational unless a causal design was specified.
```

Avoid:

- "Proves"
- "Causes" unless causality is justified
- "Risk ratio" for odds ratios or hazard ratios
- Reporting p-values without effect sizes and uncertainty
