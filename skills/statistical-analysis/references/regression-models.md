# Regression Models in R

Use this reference to choose and fit regression models after data audit and descriptive summaries are complete. Always align the model with outcome scale, study design, missing-data policy, and the user's scientific question.

## 1. Model Selection Checklist

Before fitting, identify:

- Outcome variable, scale, and distribution.
- Main exposure/predictor and adjustment covariates.
- Unit of observation and independence assumptions.
- Grouping, clustering, repeated measures, paired data, or longitudinal structure.
- Offset/exposure time for rates.
- Censoring and event time for survival outcomes.
- Whether the goal is explanation/inference or prediction.
- Minimum sample size and sparse cells, especially for categorical predictors.

If these are unknown, produce the audit and state which model decision remains unresolved.

## 2. Formula and Data Preparation

Build model data explicitly and validate formula variables:

```r
outcome <- "y"
predictors <- c("x", "age", "sex")
model_vars <- c(outcome, predictors)

stopifnot(all(model_vars %in% names(dat_clean)))
dat_model <- dat_clean[stats::complete.cases(dat_clean[, model_vars]), model_vars, drop = FALSE]

fml <- stats::as.formula(paste(outcome, "~", paste(predictors, collapse = " + ")))
stopifnot(all(all.vars(fml) %in% names(dat_model)))
```

For categorical predictors:

```r
dat_model$sex <- factor(dat_model$sex)
dat_model$sex <- stats::relevel(dat_model$sex, ref = "Female")
```

## 3. Linear Regression

Use for approximately continuous outcomes when the relationship can be represented on the outcome scale:

```r
fit_lm <- stats::lm(fml, data = dat_model)
summary(fit_lm)
stats::confint(fit_lm)
```

Minimum diagnostics:

- Residual versus fitted plot.
- Q-Q plot or residual distribution review.
- Influential observations with Cook's distance.
- Collinearity review when predictors are related.
- Nonlinearity check for continuous predictors.

```r
plot(fit_lm, which = 1)
plot(fit_lm, which = 2)
cooks <- stats::cooks.distance(fit_lm)
```

When assumptions are weak, consider transformation, spline terms, robust standard errors, quantile regression, or a model aligned to the outcome distribution.

## 4. Logistic Regression

Use for binary outcomes coded as 0/1, FALSE/TRUE, or two-level factors:

```r
fit_logit <- stats::glm(fml, data = dat_model, family = stats::binomial())
summary(fit_logit)

or <- exp(stats::coef(fit_logit))
ci <- exp(stats::confint(fit_logit))
```

Minimum checks:

- Outcome event count and events per predictor.
- Complete or quasi-complete separation.
- Sparse categorical levels.
- Calibration/discrimination when prediction performance matters.
- Linearity in the logit for continuous predictors when inference depends on it.

Interpretation:

- Coefficients are log-odds.
- `exp(coef)` gives odds ratios.
- Avoid calling odds ratios risk ratios unless a risk-ratio model or marginal effect calculation was used.

## 5. Count Regression

Use for nonnegative integer outcomes:

```r
fit_pois <- stats::glm(fml, data = dat_model, family = stats::poisson())
summary(fit_pois)

irr <- exp(stats::coef(fit_pois))
ci <- exp(stats::confint(fit_pois))
```

If modeling rates, include an offset:

```r
fit_rate <- stats::glm(
  count ~ x + age + offset(log(person_time)),
  data = dat_model,
  family = stats::poisson()
)
```

Check overdispersion:

```r
dispersion <- sum(stats::residuals(fit_pois, type = "pearson")^2) / stats::df.residual(fit_pois)
```

If dispersion is materially above 1, consider quasi-Poisson, robust SEs, or negative binomial (`MASS::glm.nb()` if available). Consider zero-inflated models only when excess zeros have a plausible data-generating explanation.

## 6. Ordinal and Multinomial Outcomes

Use ordinal regression when outcome levels are ordered:

```r
if (!requireNamespace("MASS", quietly = TRUE)) {
  stop("Package MASS is required for ordinal regression with polr().")
}
fit_ord <- MASS::polr(fml, data = dat_model, Hess = TRUE)
summary(fit_ord)
```

Use multinomial regression for unordered outcomes, usually via `nnet::multinom()` if available. Do not convert unordered categories into numeric scores unless the user explicitly defines that score as meaningful.

## 7. Survival Regression

Use Cox regression when data include follow-up time and event indicator:

```r
if (!requireNamespace("survival", quietly = TRUE)) {
  stop("Package survival is required for Cox regression.")
}
surv_fml <- survival::Surv(time, event) ~ x + age + sex
fit_cox <- survival::coxph(surv_fml, data = dat_model)
summary(fit_cox)
survival::cox.zph(fit_cox)
```

Minimum checks:

- Event coding and censoring definition.
- Time origin and follow-up units.
- Proportional hazards assumption.
- Sparse events per predictor.

Interpretation:

- `exp(coef)` gives hazard ratios.
- Do not interpret hazard ratios as risk ratios without context.

## 8. Mixed Effects, GEE, and Clustered Data

Use clustered/repeated-measure methods when rows are not independent:

- Random intercept/slope mixed models for subject/site/cluster-specific effects.
- GEE for population-average effects.
- Cluster-robust standard errors when the model mean structure is adequate but SEs need clustering.

Example with `lme4` if available:

```r
if (!requireNamespace("lme4", quietly = TRUE)) {
  stop("Package lme4 is required for this mixed-effect model.")
}
fit_lmer <- lme4::lmer(y ~ x + age + (1 | subject_id), data = dat_model)
summary(fit_lmer)
```

For binary clustered outcomes:

```r
fit_glmer <- lme4::glmer(y ~ x + age + (1 | subject_id), data = dat_model, family = stats::binomial())
summary(fit_glmer)
```

Do not add random effects only because a variable exists; justify them from repeated observations, clustering, or hierarchical sampling.

## 9. Robust and Flexible Terms

Use these when indicated by design or diagnostics:

- Robust standard errors: heteroskedasticity or clustering concerns.
- Splines: nonlinear continuous predictor effects.
- Interactions: effect modification specified by the research question.
- Penalized regression: high-dimensional predictors or prediction tasks with validation.

Interaction pattern:

```r
fit_int <- stats::lm(y ~ exposure * group + age + sex, data = dat_model)
```

Interpret interactions with predicted values or marginal contrasts when possible; main effects are conditional on reference levels and zero points.

## 10. Model Comparison

Use model comparison only for models fit to the same outcome and compatible rows:

- Nested linear or GLM models: likelihood-ratio tests or ANOVA when assumptions fit.
- AIC/BIC for relative model fit, not proof of truth.
- Cross-validation for prediction-focused comparisons.
- Avoid comparing models fit on different complete-case subsets without stating the row differences.

```r
stats::AIC(fit1, fit2)
stats::anova(fit1, fit2, test = "Chisq")
```

## 11. Output Tables

For every model, produce a structured table with:

- term
- estimate on model scale
- transformed estimate when useful: OR, IRR, HR
- standard error
- confidence interval
- p-value when appropriate
- sample size and number of events for binary/survival models
- notes on missing rows and reference levels

Base R extraction pattern:

```r
coef_tbl <- as.data.frame(summary(fit_lm)$coefficients)
coef_tbl$term <- rownames(coef_tbl)
rownames(coef_tbl) <- NULL
```
