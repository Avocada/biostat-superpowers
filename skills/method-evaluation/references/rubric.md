# Statistical Method Evaluation Rubric

Use this rubric to assign a readiness rating and prioritize recommendations.

## Rating Scale

- `ready`: The method is appropriate for the stated goal, assumptions have credible evidence, diagnostics are acceptable, stress tests do not materially change conclusions, and comparisons were fair.
- `conditionally_ready`: The method is usable with clearly stated caveats or minor follow-up checks. No known issue is likely to reverse the main conclusion or invalidate deployment.
- `needs_revision`: Important assumptions, diagnostics, robustness checks, or comparisons are incomplete. The method may become acceptable after targeted revisions.
- `not_ready`: A fatal design, leakage, validation, data-quality, identifiability, or interpretation problem makes the method unsuitable for the stated use.
- `insufficient_information`: The method cannot be evaluated because the target, data contract, model specification, validation design, or results are missing.

## Evaluation Dimensions

Score each dimension as `low risk`, `moderate risk`, `high risk`, or `critical risk`.

1. Specification
   - Target, estimand or metric, population, time horizon, and unit of analysis are explicit.
   - Causal, predictive, descriptive, and forecasting claims are not mixed without justification.

2. Data and preprocessing dependency
   - Data-quality, missingness, outlier, leakage, and split decisions are known or routed to `data-understanding-preprocessing`.
   - Preprocessing is trained only on permitted training data.

3. Method fit to objective
   - Outcome scale, design, dependence structure, censoring, clustering, and metric support the method.
   - Baselines are defined before complex models.

4. Assumptions and diagnostics
   - Assumptions are named, testable where possible, and linked to diagnostics.
   - Diagnostics are method-specific rather than generic.

5. Robustness and sensitivity
   - Stress tests cover influential units, missingness policy, preprocessing, validation design, hyperparameters, distribution shift, and method-specific failure modes.
   - Conclusions are stable across defensible alternatives.

6. Comparison fairness
   - Methods use compatible data, features, metrics, and validation schemes.
   - AIC/BIC, likelihood tests, cross-validation, holdout metrics, and bootstrap intervals are used only where appropriate.

7. Interpretation and reporting
   - Effect scales, uncertainty, limitations, and residual assumptions are stated.
   - Causal claims are limited to designs that justify them.

8. Reproducibility and implementation handoff
   - Required code, diagnostics, validation, and output artifacts are delegated to `statistical-analysis` when implementation is needed.
   - Open questions and blocking items are explicit.

## Severity Guide

- `critical`: Invalidates the main conclusion or causes severe leakage, wrong target, broken validation, unsupported causal claim, or unusable deployment.
- `high`: Could materially change conclusions, rankings, uncertainty, or decision thresholds.
- `medium`: Important caveat or missing check, but unlikely to fully invalidate the method alone.
- `low`: Documentation, clarity, or secondary diagnostic improvement.

## Readiness Decision Rule

- Any critical unresolved issue -> `not_ready`.
- Any missing target, validation design, method specification, or result summary -> `insufficient_information`.
- Multiple high unresolved issues -> `needs_revision`.
- High issues with a concrete mitigation plan and no fatal threat -> `conditionally_ready`.
- Only low or controlled medium issues after diagnostics and stress tests -> `ready`.
