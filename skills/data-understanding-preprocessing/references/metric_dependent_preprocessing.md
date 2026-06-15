# Estimand- and Metric-Aligned Preprocessing

Align preprocessing with what you are actually trying to estimate.

- **Inferential / causal goals:** align with the **effect measure and estimand**. Avoid choices
  that distort it — do not dichotomize a continuous outcome to "simplify", do not transform an
  outcome whose effect you must report on its natural scale without a back-transform plan, and
  preserve exposure/offset terms for rates. The "metric" is the estimand, not a score.
- **Predictive / prognostic goals (e.g. a TRIPOD clinical prediction model):** align with the
  **evaluation metric** below, and choose thresholds, calibration, and resampling on validation
  data only.

In both cases: never choose thresholds, clipping bounds, category groupings, or target transforms
after inspecting final test/external performance.

## Predictive evaluation metrics

## Regression

- RMSE: sensitive to large errors; inspect outliers carefully and consider target transforms only with correct inverse-transform evaluation.
- MAE: more robust to outliers; median-oriented baselines are strong.
- RMSLE or log-scale metrics: targets and predictions must be non-negative; consider log1p target transforms and clip invalid predictions.
- MAPE or percentage errors: near-zero targets can dominate; define zero handling.
- Quantile loss: preserve conditional distribution and choose quantile-specific baselines.

## Classification

- Log loss: requires well-calibrated probabilities and careful handling of rare classes.
- AUC: ranking quality matters; probability calibration may be secondary.
- Accuracy: can be misleading under class imbalance; preserve class balance in validation.
- F1, precision, recall: threshold selection belongs on validation data only.
- PR AUC: useful for rare positives; stratification and positive-class definition are critical.
- Brier score or calibration metrics: calibration plots and probability calibration may be required.

## Count, Rate, and Survival

- Count metrics: preserve exposure or offset variables when applicable.
- Rate models: define denominator and avoid leakage in exposure construction.
- Survival or time-to-event metrics: handle censoring explicitly and avoid using post-event variables.

## Preprocessing Implications

- Choose imputation, outlier treatment, clipping, target transforms, class weighting, resampling, and calibration based on the metric.
- Do not choose thresholds, clipping bounds, category groupings, or target transformations after inspecting final test performance.
- Record the metric and the preprocessing decisions it changes.
