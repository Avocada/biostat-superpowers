# Machine Learning Prediction Evaluation Template

Use for prediction-focused classification, regression, regularized models, tree ensembles, calibrated probabilities, and high-dimensional feature sets.

## Specify

- Prediction target, prediction time, deployment population, and scoring cadence.
- Primary metric and secondary metrics.
- Train/validation/test design, including time, group, stratification, and hidden-test constraints.
- Feature availability rules and preprocessing boundaries.

## Assumptions

- Validation split represents deployment.
- No leakage from future data, target construction, preprocessing, feature selection, tuning, or threshold selection.
- Metric matches business or scientific decision.
- Probability outputs are calibrated when used as probabilities.
- Feature distributions and category levels are stable enough for deployment or monitored.

## Diagnostics

- Baseline comparison: null, domain, and simple statistical model.
- Calibration curves, Brier score, log loss, reliability by subgroup for probability models.
- Error analysis by subgroup, time period, site, and outcome prevalence.
- Feature importance stability and high-risk feature review.
- Learning curves for data sufficiency.
- Threshold sensitivity for precision, recall, F1, and cost-based decisions.

## Stress Tests

- Time-aware or group-aware validation versus random validation.
- Feature group ablations, especially leakage-prone or proxy groups.
- Seed and fold stability for tuning and selected model.
- Distribution shift by time, site, subgroup, or new categories.
- Preprocessing perturbations: rare-level threshold, imputation, scaling, outlier treatment.
- Calibration under shifted prevalence.

## Compare

- Use identical splits, metrics, and feature availability.
- Compare simple baseline before complex model.
- Use nested cross-validation when tuning and performance estimation would otherwise share data.
- Report uncertainty around metric differences when feasible.

## Improve

- Simplify if complex model gains are small or unstable.
- Calibrate probabilities when decisions use risk scores.
- Add monitoring for drift and calibration.
- Remove or quarantine suspect proxy/leakage features.
- Tune thresholds only on validation data, not final test data.
