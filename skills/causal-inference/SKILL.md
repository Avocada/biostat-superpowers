---
name: causal-inference
description: >
  Use this skill to estimate the causal effect of an exposure/treatment on an outcome from
  observational (non-randomized) data — or to decide whether a causal claim is even identifiable.
  It covers the estimand and target-trial framing, causal diagrams (DAGs) and adjustment-set
  selection (confounders vs colliders vs mediators), positivity/overlap, and estimators:
  regression adjustment, propensity-score matching/weighting (IPTW), doubly-robust (AIPW/TMLE),
  difference-in-differences, instrumental variables, regression discontinuity, and g-methods for
  time-varying confounding. It also covers sensitivity to unmeasured confounding (E-value,
  negative controls). Use it whenever someone asks "does X cause Y?", mentions confounding,
  propensity scores, matching, IPTW, DAGs, target-trial emulation, or wants to adjust an
  observational comparison for a causal interpretation.
---

# Causal Inference

Estimate effects, not just associations — and refuse to dress an association up as an effect when
the data cannot identify one. The central question is always: **under what assumptions does this
analysis recover the causal estimand, and are those assumptions plausible here?**

> This skill owns *identification* (what to adjust for and whether the effect is recoverable) and
> *estimator choice*. Hand cohort construction, time-zero, and leakage to
> `data-understanding-preprocessing`; missing confounders to `missing-data`; the actual model
> fitting to `statistical-analysis`; and the final "is this trustworthy?" critique to
> `method-evaluation`. For purely predictive goals (no intervention), use `predictive-modeling`
> instead — prediction does not need identification.

## Core workflow

1. **Define the causal estimand — emulate a target trial.** Specify eligibility, the treatment
   strategies being compared, time zero (when eligibility, treatment assignment, and follow-up
   start coincide), the outcome, the causal contrast (ATE, ATT, risk difference, risk ratio,
   hazard-of-... with care), and the population the effect refers to. Misaligned time zero is the
   most common fatal error (immortal-time bias). See `references/identification-with-dags.md`.
2. **Draw the DAG and choose the adjustment set.** Encode the assumed causal structure. Use a
   backdoor criterion (or `dagitty`/`ggdag`) to find a sufficient adjustment set. **Adjust for
   confounders; never condition on colliders or on mediators** (unless decomposing direct/indirect
   effects deliberately). Do not put post-treatment variables in the model.
3. **Check positivity / overlap.** Every covariate pattern must have a non-trivial probability of
   each treatment. Inspect the propensity-score distributions by group; trim or restrict where
   overlap fails, and state the estimand implication.
4. **Choose an identification strategy and estimator** (map below) based on what makes the
   no-unmeasured-confounding assumption plausible — adjustment, or a design-based strategy
   (DiD/IV/RD) that leans on a different assumption. See `references/estimators-and-sensitivity.md`.
5. **Estimate**, with the fitting delegated to `statistical-analysis`. Report the effect on an
   interpretable scale (prefer risk difference/ratio over odds ratios for common outcomes; be
   cautious interpreting hazard ratios as causal contrasts under non-proportionality).
6. **Diagnose the design**, not just the model: covariate balance after weighting/matching
   (standardized mean differences), effective sample size and extreme weights, overlap, and
   timing checks.
7. **Stress-test the causal claim.** Sensitivity to unmeasured confounding (**E-value**, Rosenbaum
   bounds), negative-control outcomes/exposures, alternative adjustment sets, alternative time-zero
   and eligibility definitions, and trimming/caliper choices. A causal conclusion that flips under
   a plausible alternative is not ready.

## Identification strategy map

| Situation | Strategy | Key assumption (the thing that can be wrong) |
|---|---|---|
| Measured confounders, good overlap | regression adjustment / PS matching / IPTW / doubly-robust | no unmeasured confounding + positivity |
| Unmeasured confounding, but a pre/post with a comparison group | difference-in-differences | parallel trends |
| A variable that shifts treatment but not outcome directly | instrumental variable | relevance + exclusion restriction + independence |
| Treatment assigned by a threshold on a running variable | regression discontinuity | continuity at the cutoff |
| Time-varying treatment with time-varying confounders affected by prior treatment | g-methods (g-formula, MSM/IPTW, g-estimation) | sequential exchangeability + positivity |

## Operating rules

- **No causal language without an identification strategy.** If identification is weak, report the
  association and say so plainly.
- **Adjustment sets come from the DAG**, not from "throw in every covariate" or stepwise selection
  — over-adjustment (colliders, mediators, instruments) introduces bias.
- **Never adjust for post-treatment variables** unless doing a pre-specified mediation analysis.
- **Positivity is not optional.** Report overlap; structural non-positivity changes the estimand.
- **Always pair the estimate with a sensitivity analysis** for unmeasured confounding.
- Prediction ability of the propensity model is not the goal — **balance** is.

## Hand-offs

- Cohort, time-zero, immortal-time, leakage → `data-understanding-preprocessing`.
- Missing confounders → `missing-data` (impute, then estimate within imputations).
- Model/estimator fitting and CIs (bootstrap for matching/weighting) → `statistical-analysis`.
- Final readiness critique → `method-evaluation` (`method-evaluation/templates/observational_causal.md`).
- Pure prediction (no intervention) → `predictive-modeling`.

## Output

Return: (1) the causal estimand and target-trial specification; (2) the DAG and the chosen
adjustment set with justification (and what was deliberately *not* adjusted for); (3) the
identification strategy and estimator with its key assumption; (4) overlap/positivity assessment;
(5) the effect estimate with CI on an interpretable scale; (6) balance and design diagnostics;
(7) sensitivity analyses (E-value, negative controls, alternative specifications); (8) a plain
statement of how strong the causal claim is and what would overturn it.
