# Metric Optimization, Calibration, and Thresholds

Optimizing a model means improving a *specific* metric on out-of-sample data — honestly. This is
where clinical prediction modeling and score-optimization / competition work use the same
machinery; only the scoreboard differs.

## Align everything to the metric (and the decision)

- **Ranking matters, probabilities secondary:** AUC / PR-AUC (PR-AUC for rare positives).
- **Probabilities drive a decision:** log loss + **calibration** (Brier score decomposes into
  calibration + refinement). A well-discriminating but miscalibrated model gives the right ranking
  and the wrong probability — dangerous for clinical thresholds.
- **Continuous outcome:** RMSE (penalizes large errors) vs MAE (robust); pick to match the cost of
  errors.
- **A fixed competition/score metric:** optimize *that* metric in tuning and model selection, and
  validate it the same leakage-safe way — do not optimize AUC and hope a different target metric
  follows.

Choose the metric from the decision/cost, then optimize and report it consistently.

## Calibration (do not skip)

```r
# R: calibration of predicted probabilities
library(rms); val <- val.prob(p = pred_prob, y = outcome)     # calibration slope/intercept, Brier
```
```python
from sklearn.calibration import calibration_curve, CalibratedClassifierCV
# recalibrate a fitted model (Platt / isotonic) inside CV:
calibrated = CalibratedClassifierCV(base_estimator, method="isotonic", cv=5).fit(X, y)
```

Report calibration slope (ideal 1) and intercept (ideal 0), plus a calibration plot. Recalibrate
(Platt/isotonic) when needed — but fit the recalibration inside the resampling, not on the test set.

## Class imbalance

Imbalance is usually a *metric and threshold* problem, not a "fix the data" problem.

- Prefer metrics robust to imbalance (PR-AUC, balanced accuracy) and **threshold tuning** over
  blunt resampling.
- If resampling/weighting helps, do it **inside the training fold only**, and **recalibrate** —
  oversampling distorts predicted probabilities.
- Report performance at the operating threshold, not just the threshold-free metric.

## Thresholds from the decision

A probability model becomes a decision via a threshold. Set it from the relative cost of false
positives vs false negatives, or use **decision-curve analysis** (net benefit across threshold
probabilities) to show clinical usefulness — not by maximizing accuracy.

## Pushing a score honestly (ensembling / stacking)

When the goal is to maximize a held-out or competition metric:

1. **Features first.** Most gains come from leakage-safe feature engineering and encoding, not
   exotic models.
2. **Regularize and early-stop** to control overfitting (especially gradient boosting).
3. **Ensemble diverse models.** Averaging/blending or **stacking** models that err differently
   (e.g. a linear model + boosted trees) usually beats any single one — provided each base model
   and the stacker are validated with the same leakage-safe scheme (out-of-fold predictions feed
   the stacker; never in-fold).
4. **Trust the validation that mirrors the target.** If the scoreboard uses a temporal or grouped
   test, your local validation must too, or the local gains will not transfer.

```python
# Python: out-of-fold stacking with leakage discipline
from sklearn.ensemble import StackingClassifier
stack = StackingClassifier(estimators=[("lr", lr_pipe), ("gb", gb_pipe)],
                           final_estimator=meta, cv=5)        # cv= produces out-of-fold meta-features
```
```r
# R: stacks package builds an ensemble from tuned tidymodels workflows
library(stacks)
ens <- stacks() |> add_candidates(res_lr) |> add_candidates(res_gb) |>
  blend_predictions() |> fit_members()
```

## The honesty line

Whether the scoreboard is a journal or a leaderboard, the same discipline applies: no leakage,
tune and select on validation only, report out-of-sample (optimism-corrected) performance, and
beat a real baseline. A score that comes from leakage is not an improvement — it is a bug that will
surface on truly unseen data.
