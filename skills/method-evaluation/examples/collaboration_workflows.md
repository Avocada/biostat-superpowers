# Collaboration Workflows

How `method-evaluation` composes with the other skills on real biomedical tasks. The pattern is
always: route data/design/implementation to the owning skill, and keep the critical-reasoning and
readiness call here.

## Example 1: Observational cohort — does drug A reduce 1-year mortality vs drug B?

1. `study-design-and-power` — state the estimand (target-trial style: eligibility, treatment
   strategies, time zero, outcome, contrast) and whether the data can support it.
2. `data-understanding-preprocessing` — eligibility, time-zero, immortal-time check, covariate
   availability at baseline, leakage audit.
3. `causal-inference` — DAG, adjustment set, positivity/overlap, estimator (IPTW / matching /
   doubly robust).
4. `missing-data` — multiple imputation for partially missing confounders; MNAR sensitivity.
5. `statistical-analysis` — fit the weighted/adjusted outcome model; HR or risk difference with CIs.
6. **`method-evaluation`** — `templates/observational_causal.md`: confounding, overlap, balance
   diagnostics, negative controls, E-value for unmeasured confounding; readiness rating.
7. `reporting-and-reproducibility` — STROBE-aligned writeup, Table 1 by exposure, effect + CI.

## Example 2: Randomized trial — binary primary outcome

1. `study-design-and-power` — confirm the pre-specified estimand, randomization, and that power
   matches the protocol.
2. `data-understanding-preprocessing` — analysis populations (ITT vs per-protocol), outcome
   ascertainment, missing-outcome handling.
3. `statistical-analysis` — primary model (often adjusted for stratification factors); risk
   difference / risk ratio / OR as pre-specified.
4. **`method-evaluation`** — `templates/experiments.md`: was the estimand respected, multiplicity
   handled, subgroup claims pre-specified, missing outcomes addressed; readiness rating.
5. `reporting-and-reproducibility` — CONSORT flow + checklist, effect with CI, pre-specified vs
   exploratory clearly separated.

## Example 3: Prognostic (clinical prediction) model — TRIPOD

1. `data-understanding-preprocessing` — leakage and time-zero discipline, internal vs external
   validation split, events-per-variable.
2. `statistical-analysis` — develop the model; produce predictions for validation.
3. **`method-evaluation`** — `templates/machine_learning_prediction.md`: discrimination AND
   **calibration**, internal validation (bootstrap optimism), external/temporal validation, fair
   baseline comparison, decision-curve relevance; readiness rating.
4. `reporting-and-reproducibility` — TRIPOD-aligned reporting of development and validation.

## Example 4: Someone hands you a fitted model to critique

A colleague reports "logistic regression of mortality on treatment, no adjustment, treatment
'works'." Run **`method-evaluation`** directly:

- `templates/regression.md` + `templates/observational_causal.md`.
- Flag: unadjusted observational comparison interpreted causally (fatal for the causal claim);
  no confounding control; OR possibly mislabeled as risk; no diagnostics; no uncertainty beyond p.
- Readiness: `not_ready` for a causal claim; route confounding to `causal-inference`, adjusted
  fitting to `statistical-analysis`, and re-evaluate.

## Example 5: Longitudinal / repeated-measures study

1. `data-understanding-preprocessing` — subject/visit grain, group-aware structure, dropout.
2. `missing-data` — dropout mechanism; MMRM or multiple imputation as appropriate.
3. `statistical-analysis` — mixed-effects or GEE; conditional vs population-average effect.
4. **`method-evaluation`** — `templates/regression.md` + `references/stress_tests.yaml`: random-
   effects justification, dropout/missingness sensitivity, cluster count, convergence; readiness.
5. `reporting-and-reproducibility` — report the dependence structure and the missing-data approach.
