# Regression Models in Python

The Python counterpart to `regression-models.md`. Use `statsmodels` for inference (it reports
coefficients, standard errors, and confidence intervals like a statistician expects) and
`lifelines` for survival. Use `scikit-learn` only when the goal is prediction, not inference.

Always align the model with outcome scale, study design, missing-data policy, and the research
question. Build the model frame explicitly and validate it before fitting.

```python
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

model_vars = ["y", "x", "age", "sex"]
assert set(model_vars).issubset(df.columns)
dat = df.dropna(subset=model_vars).copy()
dat["sex"] = pd.Categorical(dat["sex"], categories=["Female", "Male"])  # first level = reference
```

## Linear regression (continuous outcome)

```python
fit = smf.ols("y ~ x + age + C(sex)", data=dat).fit()
print(fit.summary())
fit.conf_int()                      # 95% CIs
# Heteroskedasticity-robust SEs:
fit_hc = smf.ols("y ~ x + age + C(sex)", data=dat).fit(cov_type="HC3")
```

Diagnostics: residuals-vs-fitted and Q-Q (`statsmodels.graphics`), influence
(`fit.get_influence().cooks_distance`), multicollinearity
(`statsmodels.stats.outliers_influence.variance_inflation_factor`). Consider splines
(`patsy` `bs()`/`cr()`), transforms, or quantile regression (`smf.quantreg`) when assumptions fail.

## Logistic regression (binary outcome)

```python
fit = smf.logit("y ~ x + age + C(sex)", data=dat).fit()
print(fit.summary())
or_tbl = np.exp(pd.concat([fit.params, fit.conf_int()], axis=1))
or_tbl.columns = ["OR", "CI_low", "CI_high"]
```

Checks: events-per-variable, separation (watch for "perfect separation" warnings — consider
penalized/Firth via `logistf` in R or a regularized fit), sparse cells, calibration/AUC only when
prediction matters. Coefficients are log-odds; `exp()` gives odds ratios — **not** risk ratios.

**Risk ratio / risk difference when wanted:** modified Poisson with robust SEs —
`smf.glm("y ~ x", data=dat, family=sm.families.Poisson()).fit(cov_type="HC0")`, then `exp(coef)`
is the risk ratio; or compute marginal effects.

## Count / rate regression

```python
fit_pois = smf.glm("count ~ x + age", data=dat, family=sm.families.Poisson()).fit()
irr = np.exp(fit_pois.params)
# Overdispersion:
pearson = (fit_pois.resid_pearson ** 2).sum() / fit_pois.df_resid
# Rate model with exposure time:
fit_rate = smf.glm("count ~ x + age", data=dat, family=sm.families.Poisson(),
                   offset=np.log(dat["person_time"])).fit()
# If overdispersed, negative binomial:
fit_nb = smf.glm("count ~ x + age", data=dat, family=sm.families.NegativeBinomial()).fit()
```

If dispersion is materially above 1, do not trust naive Poisson SEs (use NB, quasi-Poisson-style
robust SEs, or `cov_type="HC0"`).

## Ordinal and multinomial outcomes

```python
from statsmodels.miscmodels.ordinal_model import OrderedModel
fit_ord = OrderedModel(dat["y_ord"], dat[["x", "age"]], distr="logit").fit(method="bfgs")

fit_multi = smf.mnlogit("y_nom ~ x + age", data=dat).fit()   # unordered outcome
```

Do not convert unordered categories to numeric scores. Check the proportional-odds assumption for
ordinal models.

## Survival regression (time-to-event)

```python
from lifelines import CoxPHFitter, KaplanMeierFitter

km = KaplanMeierFitter().fit(dat["time"], dat["event"])      # event: 1=event, 0=censored
cph = CoxPHFitter().fit(dat[["time", "event", "x", "age"]], duration_col="time", event_col="event")
cph.print_summary()                                          # exp(coef) = hazard ratio
cph.check_assumptions(dat, show_plots=False)                 # proportional hazards
```

Checks: event coding and censoring, time origin and units, proportional hazards, events-per-
variable. `exp(coef)` is a hazard ratio — not a risk ratio. With **competing events**, decide the
estimand *before* the model: a **cause-specific** hazard (a Cox model that censors competing
events; for etiologic questions) vs **cumulative incidence** (Aalen–Johansen CIF, or a **Fine–Gray**
subdistribution model; for absolute risk / prediction). They answer different questions — don't
default to one. (R `survival`/`cmprsk`; Python `lifelines` competing-risks tools.)

## Mixed effects, GEE, clustered data

```python
# Random intercept (continuous outcome):
fit_lmm = smf.mixedlm("y ~ x + age", data=dat, groups=dat["subject_id"]).fit()

# Population-average effects via GEE (e.g. binary, exchangeable working correlation):
import statsmodels.genmod.generalized_estimating_equations as gee
fit_gee = smf.gee("y ~ x + age", groups="subject_id", data=dat,
                  family=sm.families.Binomial(), cov_struct=sm.cov_struct.Exchangeable()).fit()

# Or cluster-robust SEs on a GLM when the mean model is adequate:
fit_cr = smf.glm("y ~ x + age", data=dat, family=sm.families.Binomial()).fit(
    cov_type="cluster", cov_kwds={"groups": dat["subject_id"]})
```

Do not add random effects just because a grouping variable exists — justify them from repeated
observations, clustering, or hierarchical sampling. Report cluster count and convergence warnings.

## Model comparison & tables

- Nested models: likelihood-ratio test (`fit.compare_lr_test`), or `sm.stats.anova_lm` for OLS.
- AIC/BIC (`fit.aic`, `fit.bic`) for relative fit among compatible likelihood models — not proof.
- Cross-validation for prediction-focused comparison only.
- Export a tidy table: `term, estimate, transformed (OR/IRR/HR), SE, CI, p, n, n_events`. Build it
  from `fit.params`, `fit.bse`, `fit.conf_int()`, `fit.pvalues`. Save as CSV and keep the
  `fit.summary()` text alongside.
