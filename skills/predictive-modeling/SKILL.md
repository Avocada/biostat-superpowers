---
name: predictive-modeling
description: >
  Use this skill when the goal is PREDICTION rather than explanation or causation — building a
  model that predicts an outcome well on new data, and optimizing a chosen performance metric. In
  biomedical research this is a clinical prediction / prognostic model (develop, validate, report
  per TRIPOD/PROBAST); the same machinery generalizes to any predictive task, including optimizing
  a target score on a held-out set or a competition. It covers leakage-safe resampling and
  splitting, model classes (regularized regression, tree ensembles/boosting), hyperparameter
  tuning by (nested) cross-validation, discrimination AND calibration, internal validation
  (bootstrap optimism), external/temporal validation, fair baseline comparison, metric
  optimization, ensembling/stacking, and decision thresholds. Use it for "build a model to predict
  X", "improve my model's score/AUC", "validate this prediction model", "tune hyperparameters", or
  "is my model overfitting?".
---

# Predictive Modeling

When the goal is to predict well on data you have not seen — not to estimate an effect — the rules
change. You no longer need an identification strategy; you need **honest out-of-sample performance**
and **no leakage**. This skill builds, tunes, validates, and reports predictive models, with
clinical prediction models (TRIPOD) as the biomedical flagship and generic score-optimization
(including competitions) as the same workflow with a different scoreboard.

> Prediction is not causation: a feature can predict an outcome and have no causal relationship to
> it. Do not interpret predictive importance as effect. For causal questions use `causal-inference`;
> for inferential effect estimates use `statistical-analysis`.

## Core workflow

1. **Define the prediction task and the scoreboard.** Outcome, prediction time (what is known
   when), the population the model will be used on, and the **metric you are optimizing** (and why
   it matches the decision): AUC/PR-AUC, log loss, Brier, calibration, RMSE/MAE, or a competition
   metric. For clinical use, the decision context sets the metric and the operating threshold.
2. **Lock leakage-safe data handling first.** Route to `data-understanding-preprocessing` for the
   split/validation design: everything learned (imputation, scaling, encoding, feature selection,
   target encoding) is fit **inside** the resampling fold, never on the full data. Same-subject/
   site rows must not straddle train and test; temporal tasks use time-based splits. Leakage is the
   #1 cause of a great validation score that collapses in the real world.
3. **Size the problem.** For clinical models, check events-per-variable / use `pmsampsize`; for any
   task, make sure the validation set can actually estimate the metric with usable precision.
4. **Pick model classes by the data, not by hype.** Regularized regression (ridge/lasso/elastic
   net) is a strong, calibratable baseline; gradient-boosted trees (XGBoost/LightGBM) and random
   forests excel on tabular interactions; keep a simple baseline (a clinical score, logistic
   regression, or the majority/mean) to beat. See `references/validation-and-overfitting.md`.
5. **Tune by (nested) cross-validation.** Select hyperparameters on inner folds; estimate
   performance on outer folds or a held-out set the tuning never saw. Tuning on the same data you
   report performance on is optimistic and wrong.
6. **Assess discrimination AND calibration.** Discrimination (AUC/c-index) is not enough — a model
   that ranks well can still give miscalibrated probabilities that mislead a clinical decision.
   Report a calibration plot / slope / intercept. See `references/metric-optimization.md`.
7. **Validate honestly.** Internal validation with the **bootstrap to estimate optimism** (Harrell)
   or repeated CV; then **external / temporal / geographic validation** when claiming
   transportability. Report the optimism-corrected performance, not the apparent (training) one.
8. **Compare fairly and (if optimizing a score) push the metric.** Compare against the baseline on
   the same data and metric. To improve the score: better features and leakage-safe encoding,
   regularization/early stopping, calibration, and **ensembling/stacking** of diverse models —
   each validated the same way. See `references/metric-optimization.md`.
9. **Set the operating threshold from the decision, not the data alone** (decision-curve analysis,
   cost-weighted), and report performance at it.

## Operating rules

- **No leakage, ever.** Fit all learned transforms inside the fold; respect subject/time
  boundaries; never let the test set touch tuning or feature selection.
- **Report optimism-corrected, out-of-sample performance** — apparent performance is not a result.
- **Calibration is part of performance**, not optional, whenever probabilities drive a decision.
- **Always beat a real baseline** (clinical score / simple model), reported on the same metric.
- **Tune and select on validation, never on the final test/external set.**
- **Predictive ≠ causal ≠ important.** Feature importance is about prediction, not effect.
- For clinical models, plan development *and* validation up front and report per **TRIPOD**;
  appraise risk of bias with **PROBAST**.

## Goal-driven iterative optimization (works with `/goal`)

`/goal` (on Claude and Codex) pursues a target until it is met — a natural fit for "improve the
model until metric X ≥ Y". This skill makes that loop *rigorous* rather than a path to a
self-deceiving score:

- **State a measurable target and a stopping rule up front:** the metric, the validation scheme it
  is measured on, the threshold, and a plateau rule (e.g. stop after N rounds with no out-of-fold
  gain). `/goal` needs a concrete finish line.
- **Quarantine a final test set and touch it once,** at the very end. The loop never sees it.
- **Optimize and select only on the (nested) CV / validation fold;** each iteration re-fits all
  preprocessing inside the fold, so no leakage creeps in across rounds.
- **Beware adaptive overfitting:** repeatedly tuning toward the same validation set is itself a
  form of leakage — the score drifts above true performance. Bound the number of evaluations,
  prefer nested CV, and confirm the final model on the untouched test/external set.
- **Calibration is part of the goal,** not just discrimination.
- **Log every round** (what changed, out-of-fold metric, whether it generalized) and stop when the
  goal is met *and* holds — or when rounds plateau.

See `examples/goal-driven-optimization.md` for a full `/goal` walkthrough.

## Hand-offs

- Split/validation design, leakage audit, feature availability → `data-understanding-preprocessing`.
- Effect estimation / inference (not prediction) → `statistical-analysis`.
- Causal effect of a feature (not its predictive value) → `causal-inference`.
- Missing predictors → `missing-data` (impute inside the resampling fold).
- "Is this validation trustworthy?" critique → `method-evaluation`
  (`method-evaluation/templates/machine_learning_prediction.md`).
- TRIPOD-aligned reporting of development & validation → `reporting-and-reproducibility`.

## Output

Return: (1) the prediction task, prediction-time contract, and target metric with rationale;
(2) the leakage-safe split/resampling design; (3) model classes tried and the baseline; (4) the
tuning procedure (nested CV); (5) discrimination and calibration; (6) internal (optimism-corrected)
and external validation results; (7) fair comparison vs baseline and any ensembling; (8) the chosen
operating threshold and its justification; (9) reproducible code (R `tidymodels` / Python
`scikit-learn`) and TRIPOD-relevant reporting items.
