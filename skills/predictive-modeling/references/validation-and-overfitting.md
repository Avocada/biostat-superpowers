# Validation and Overfitting

The whole game in prediction is estimating performance on data the model has not seen, without
fooling yourself. Two failure modes dominate: **leakage** (information from the test set or the
future sneaks into training) and **optimism** (reporting performance on the same data used to build
or tune the model).

## Leakage-safe resampling (the cardinal rule)

Every learned step — imputation, scaling, encoding, feature selection, target/mean encoding,
oversampling — must be fit **inside** each training fold, then applied to the held-out fold. Fit
them once on the whole dataset and your CV score is optimistic and the real-world score will drop.

```r
# R: tidymodels keeps preprocessing inside resampling automatically via a recipe + workflow
library(tidymodels)
rec  <- recipe(outcome ~ ., data = train) |>
  step_impute_bag(all_predictors()) |> step_normalize(all_numeric_predictors()) |>
  step_dummy(all_nominal_predictors())
wf   <- workflow() |> add_recipe(rec) |> add_model(logistic_reg(penalty = tune(), mixture = 1) |>
                                                   set_engine("glmnet"))
folds <- vfold_cv(train, v = 10, strata = outcome)        # group_vfold_cv() for clustered data
res   <- tune_grid(wf, resamples = folds, grid = 20, metrics = metric_set(roc_auc, brier_class))
```

```python
# Python: put preprocessing in a Pipeline so it is refit inside every CV fold
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import StratifiedKFold, cross_val_score
pipe = Pipeline([("prep", ColumnTransformer(...)), ("clf", model)])
cv = StratifiedKFold(n_splits=10, shuffle=True, random_state=0)   # GroupKFold for clustered data
cross_val_score(pipe, X, y, cv=cv, scoring="roc_auc")             # prep refit each fold
```

Use **GroupKFold** when rows share a subject/site, and a **time-based split** (no shuffling) when
the task is temporal — random CV on temporal data leaks the future.

## Tuning without cheating — nested CV

Selecting hyperparameters and reporting performance on the same folds is optimistic. Use **nested
cross-validation**: an inner loop tunes, an outer loop estimates performance the tuning never saw.
Equivalently, hold out a final test set (or external dataset) that is touched exactly once, at the
end.

## Internal validation: bootstrap optimism (Harrell)

For clinical prediction models the recommended internal-validation method is the **bootstrap
optimism correction**: fit on a bootstrap sample, measure performance on the bootstrap and on the
original data, and subtract the average difference (the optimism) from the apparent performance.
R: `rms::validate()` / `rms::calibrate()`. This corrects the over-optimism of apparent performance
without wasting data on a single split.

## External / temporal / geographic validation

Internal validation estimates reproducibility in the same setting; **transportability** requires
validating in a different time, site, or population. Report discrimination and calibration in the
external set separately. A model that validates internally but not externally is common and worth
catching before deployment.

## Sample size for prediction

Do not eyeball it. For clinical prediction models use `pmsampsize` (R) to get the minimum sample
for the number of predictors and outcome prevalence (it targets small optimism and adequate
calibration), and respect events-per-variable rules of thumb as a floor, not a target.

## Symptoms of overfitting

- Apparent (training) performance ≫ cross-validated performance.
- Performance drops sharply from internal to external validation.
- Calibration slope < 1 (predictions too extreme) — a classic sign of overfitting.
- A model with many features and few events; unstable coefficients across folds.

Remedies: regularization (ridge/lasso/elastic net), fewer/penalized features, early stopping for
boosting, and shrinkage/recalibration of the final model.
