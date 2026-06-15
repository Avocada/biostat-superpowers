# Reviewer evidence checklist

"We used biostat-superpowers" is **not** evidence that an analysis is correct. This checklist is the
bar the suite holds an analysis to — the artifacts a manuscript should be able to *show*. Editors and
reviewers can use it as a request list; authors can use it as a pre-submission gate.

The point is to move the conversation from *"we used a tool"* to *"here is what the tool required us
to demonstrate."*

## For any analysis
- [ ] **Estimand stated in one sentence** — population, exposure/treatment contrast, outcome, time
  horizon, and how intercurrent events are handled (ICH E9(R1) thinking).
- [ ] **Design and eligibility** — inclusion/exclusion, **time zero**, and (observational) a
  target-trial description; a participant-flow / attrition count.
- [ ] **Effect reported as estimate + CI on a named scale** (risk difference, RR, OR, HR), with the
  scale labeled correctly; **absolute and relative** where possible. P-values are context, not the result.
- [ ] **Reporting guideline** followed and cited (CONSORT / STROBE / TRIPOD / PRISMA / STARD).
- [ ] **Reproducibility** — code, random seed, environment/package versions, and a data-availability
  statement.

## If the claim is causal (observational)
- [ ] **DAG / adjustment set** — what was adjusted for and what was deliberately *not* (no
  post-treatment variables, mediators, or colliders).
- [ ] **Positivity / overlap** assessed; **covariate balance** (standardized mean differences)
  reported after matching/weighting.
- [ ] **Estimator** named (regression adjustment / PS matching / IPTW / doubly-robust / DiD / IV / RD)
  with its key identifying assumption stated.
- [ ] **Sensitivity to unmeasured confounding** — an **E-value** and/or negative-control results.

## If there is missing data
- [ ] **Amount and pattern** reported; **mechanism assumption** (MCAR/MAR/MNAR) stated with rationale.
- [ ] **Method** named (multiple imputation with Rubin's rules; or a likelihood/MMRM approach) — not a
  silent complete-case drop, not single mean imputation for the primary inferential model.
- [ ] **MNAR sensitivity analysis** when outcome-dependent missingness is plausible.

## If it is a prediction model
- [ ] **Leakage audit** — no feature unavailable at prediction time; preprocessing fit inside CV folds.
- [ ] **Discrimination AND calibration** reported (not AUC alone).
- [ ] **Internal validation** (optimism-corrected, e.g. bootstrap) **and external/temporal** validation
  when transportability is claimed; sample size / events-per-variable justified (TRIPOD/PROBAST).

## Triaging partial compliance

Not every gap is equal — tier them (this maps to the suite's readiness rubric, so it doubles as a
reviewer decision aid):

- **Fatal (→ reject / not ready):** no defined estimand; a causal claim with no identification
  strategy or adjustment; data leakage; conditioning on post-treatment variables; tuning on the test
  set; outcome-dependent missingness ignored.
- **Serious (→ major revision):** no positivity/overlap or balance diagnostics; single imputation for
  a primary inferential model; discrimination reported without calibration; no sensitivity analysis
  for a causal claim.
- **Minor (→ routine request):** relative effects without absolute risks; incomplete
  reporting-guideline items; survival figures missing numbers-at-risk.

A manuscript that can tick these boxes is not automatically right — but one that cannot is not ready.
