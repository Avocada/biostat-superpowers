# Multiple Imputation (MICE) — R and Python

Multiple imputation by chained equations (MICE / FCS): impute each incomplete variable from the
others, repeat to build *m* completed datasets, analyze each, and pool. Valid under MAR when the
imputation model is congenial with the analysis and includes the right variables.

## The non-negotiables

1. **Include the outcome in the imputation model.** Omitting it biases associations toward the
   null. (Yes, even though you then analyze the outcome.)
2. **Include auxiliary variables** that predict missingness or the missing values — they make MAR
   more plausible and improve efficiency.
3. **Match the imputation to the analysis** (congeniality): if the analysis has interactions,
   nonlinear terms, or is multilevel, the imputation must reflect that.
4. **Respect variable type and distribution:** predictive mean matching (PMM) for skewed
   continuous, logistic for binary, polytomous for categorical, multilevel methods for clustered.
5. **Pool with Rubin's rules** — never average the imputed datasets into one and analyze that.
6. **Choose m** generously; a common rule is m ≥ the percentage of incomplete cases. Imputations
   are cheap; too few inflates Monte-Carlo error.

## R — `mice`

```r
library(mice)

# 1. Inspect pattern and choose methods/predictors
md.pattern(dat)
ini <- mice(dat, maxit = 0)            # dry run to get defaults
meth <- ini$method                     # e.g. "pmm" for numeric, "logreg" for binary
pred <- ini$predictorMatrix
# (optionally edit pred to drop IDs / add auxiliaries; quickpred() helps)

# 2. Impute: m datasets, fix the seed
imp <- mice(dat, m = 20, method = meth, predictorMatrix = pred, seed = 123)
plot(imp)                              # check convergence of the chains

# 3. Analyze within each imputation
fit <- with(imp, glm(outcome ~ exposure + age + sex, family = binomial()))

# 4. Pool (Rubin's rules)
pooled <- pool(fit)
summary(pooled, conf.int = TRUE, exponentiate = TRUE)   # OR + 95% CI
```

For multilevel/clustered data use methods like `2l.pmm` / `2l.bin`; for longitudinal trials see
reference-based imputation (`mice` + `rbmi` package) for MNAR-style sensitivity.

## Python — `IterativeImputer` (scikit-learn) and `statsmodels` MICE

`statsmodels` MICE pools with Rubin's rules out of the box, which is what you want for inference:

```python
import statsmodels.api as sm
from statsmodels.imputation import mice

imp = mice.MICEData(df)                       # df with NaNs; set perturbation/imputers per col
fml = "outcome ~ exposure + age + C(sex)"
result = mice.MICE(fml, sm.Logit, imp).fit(n_imputations=20, n_burnin=10)   # 2nd arg is a model CLASS: sm.OLS / sm.Logit / sm.GLM
print(result.summary())                       # pooled estimates + CIs
```

`sklearn`'s `IterativeImputer` produces imputations but does **not** pool — to get valid
inference, draw multiple imputations (`sample_posterior=True`, different `random_state`s), fit the
model on each, and pool manually with Rubin's rules:

```python
import numpy as np, pandas as pd
from sklearn.experimental import enable_iterative_imputer  # noqa
from sklearn.impute import IterativeImputer

Xy = pd.concat([X, y], axis=1)                 # include the OUTCOME in the imputation matrix
ests, vars = [], []
for s in range(20):
    completed = pd.DataFrame(
        IterativeImputer(sample_posterior=True, random_state=s).fit_transform(Xy),
        columns=Xy.columns)
    fit = fit_model(completed[X.columns], completed[y.name])   # refit the analysis model
    ests.append(fit.params); vars.append(fit.bse**2)

ests, vars = np.array(ests), np.array(vars)
qbar = ests.mean(0)                            # pooled estimate
ubar = vars.mean(0)                            # within-imputation variance
b = ests.var(0, ddof=1)                        # between-imputation variance
total_var = ubar + (1 + 1/len(ests)) * b       # Rubin's total variance
se = np.sqrt(total_var)
```

## MNAR sensitivity — delta / pattern-mixture

Stress the MAR assumption: impute under MAR, then shift the imputed values in the missing group by
a clinically plausible amount δ and re-analyze across a range of δ. If the conclusion is stable
across plausible δ, it is robust to that form of MNAR; if it flips, say so.

```r
# mice supports post-hoc adjustment of imputed values for delta-based sensitivity:
delta <- c(0, -1, -2)                          # plausible shifts on the outcome scale
# loop: re-impute with post-processing that adds delta to imputed cells, refit, pool, compare.
```

## Reporting checklist

Amount and pattern of missingness; assumed mechanism and rationale; software and method (e.g.
"`mice`, PMM/logreg, m = 20"); the imputation model and auxiliary variables; convergence check;
pooled estimates with CIs; and the MNAR sensitivity result. This is the paragraph reviewers expect.
