# Estimators and Sensitivity Analysis

Once the effect is identified (see `identification-with-dags.md`), choose an estimator. Fit it via
`statistical-analysis`; this file is the menu and the code patterns. Get a valid confidence
interval — for matching and weighting, use a robust/sandwich SE or the bootstrap, not the naive
model SE.

## Adjustment-based estimators (assume no unmeasured confounding + positivity)

### Regression adjustment / G-computation
Fit an outcome model conditional on treatment and the adjustment set, then average predicted
potential outcomes under "all treated" vs "all untreated" (the g-formula / standardization). This
gives a marginal effect on the scale you choose.

### Propensity-score matching
```r
library(MatchIt)
m <- matchit(treat ~ age + severity + sex, data = dat, method = "nearest", caliper = 0.2)
summary(m)                       # check standardized mean differences (aim |SMD| < 0.1)
md <- match.data(m)               # includes the matched-set id `subclass` and `weights`
# Matching induces within-set dependence: use a robust/cluster SE on the matched set
# (or bootstrap at the matched-set level). Naive model SEs are too small here.
fit <- survival::coxph(survival::Surv(time, event) ~ treat + cluster(subclass),
                       data = md, weights = weights, robust = TRUE)
```

### Inverse-probability-of-treatment weighting (IPTW)
```r
library(WeightIt); library(survey)
w <- weightit(treat ~ age + severity + sex, data = dat, method = "ps", estimand = "ATE")
# Check balance and extreme weights:
summary(w)                       # effective sample size, max weight
des <- svydesign(~1, weights = w$weights, data = dat)
fit <- svyglm(outcome ~ treat, design = des, family = quasibinomial())  # robust SEs
```
```python
# Python (zEpid or manual): estimate PS, build stabilized weights, fit weighted GLM with robust SE
import statsmodels.formula.api as smf, statsmodels.api as sm
ps = smf.logit("treat ~ age + severity + C(sex)", data=df).fit().predict()
w = np.where(df.treat==1, df.treat.mean()/ps, (1-df.treat.mean())/(1-ps))  # stabilized
fit = smf.glm("outcome ~ treat", data=df, family=sm.families.Binomial(),
              freq_weights=w).fit(cov_type="HC0")
```

### Doubly-robust (AIPW / TMLE)
Combine an outcome model and a propensity model; consistent if *either* is correct. Prefer when
feasible. R: `tmle`, `AIPW`; Python: `econml` (e.g. `LinearDML`, `DRLearner`), `zEpid`.

## Design-based strategies (trade the confounding assumption for another)

- **Difference-in-differences** — two groups, pre/post; identifies under **parallel trends**.
  Check pre-trends; consider modern staggered-adoption estimators when treatment timing varies.
- **Instrumental variables** — needs an instrument that is relevant, affects the outcome only
  through treatment (exclusion), and is as-good-as-random. Two-stage least squares / `ivreg` (R),
  `linearmodels`/`econml` (Python). Weak instruments give badly biased estimates — report the
  first-stage strength.
- **Regression discontinuity** — treatment assigned by a cutoff on a running variable; identifies
  a *local* effect at the cutoff under continuity. R: `rdrobust`; Python: `rdrobust`.

## Time-varying treatment & confounding → g-methods

When treatment changes over time and is affected by time-varying confounders that are themselves
affected by prior treatment, standard adjustment is biased *both ways*. Use the **g-formula**,
**marginal structural models (IPTW over time)**, or **g-estimation**. This is the Hernán & Robins
territory; flag it explicitly and do not fall back on a single adjusted regression.

## Sensitivity to unmeasured confounding (mandatory for a causal claim)

- **E-value** — the minimum strength of association an unmeasured confounder would need (with both
  treatment and outcome) to explain away the observed effect. Easy to report and interpret.
  ```r
  library(EValue)
  evalue(RR = 1.6, lo = 1.2, hi = 2.1)   # also OR/HR/RD variants
  ```
- **Negative controls** — an outcome (or exposure) that should have *no* effect; a non-null result
  there signals residual confounding.
- **Rosenbaum bounds** (for matched designs) — how large a hidden bias would overturn significance.
- **Alternative specifications** — adjustment set, time-zero, eligibility, trimming, caliper.

**Choose by what the data can support, not from a menu.** These checks are not equally available: an
**E-value** needs only the estimate; **negative controls** need a plausible control outcome/exposure
in your data; **high-dimensional PS** needs rich claims/utilization codes; **Rosenbaum bounds** need a
matched design. Recommend the ones the data source can actually run — and say which it cannot.

Report the estimate *with* its E-value and at least one other check. State plainly what magnitude
of unmeasured confounding would change the conclusion — that sentence is the difference between a
defensible causal claim and an overclaim.
