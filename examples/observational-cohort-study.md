# Worked example: an observational cohort study, end to end

This walks one realistic question through the whole suite, showing what each skill contributes and
how the orchestrator (`biostatistics`) hands off. It is deliberately a *hard* case — an
observational comparative-effectiveness question from EHR data, where the easy mistakes are fatal.

> **The question.** "In our EHR data, does starting **drug A** versus **drug B** reduce **1-year
> all-cause mortality** in adults with condition X?"

The orchestrator's first move: classify the goal (**causal**, observational) and state the
estimand in one sentence, then route.

---

## 1 · `study-design-and-power` — frame the estimand, emulate a target trial

- **Estimand (target trial):** among adults with X newly initiating A or B (time zero = first
  prescription), the effect of *initiating A vs B* on *all-cause death within 365 days*, as a
  **risk difference and hazard ratio**, in the population eligible for either drug.
- **Design:** new-user, active-comparator cohort (A vs B), which aligns time zero and avoids
  prevalent-user and immortal-time bias.
- **Anticipated bias:** confounding by indication (why was A vs B chosen?), informative censoring,
  missing baseline labs.
- **Feasibility:** events-driven — check that the number of deaths supports the target HR.

**Hands off** the identification details to `causal-inference` and the data build to
`data-understanding-preprocessing`.

## 2 · `data-understanding-preprocessing` — make the data trustworthy

- **Cohort & time zero:** first A-or-B prescription; require ≥1 year of prior enrollment (so
  baseline covariates are observable) and no prior use of either drug (new-user).
- **Attrition table:** 41,290 with X → 12,455 new users of A/B → 9,830 meeting eligibility →
  9,830 analyzed (each exclusion logged with a count).
- **Leakage / immortal-time audit:** drop any covariate measured after time zero; confirm the
  outcome (death) is ascertained identically in both arms; flag "received second prescription" as
  a post-baseline variable that must **not** be a covariate.
- **Roles & types:** exposure (A/B), outcome (death + follow-up time + censoring), confounders
  (age, sex, comorbidity index, baseline labs, prior healthcare use), IDs, time variables.
- **Missingness:** baseline creatinine missing in 18% → routed to `missing-data` (not dropped).

Output: an analysis-ready table spec + a column action table. **Hands off** missingness to
`missing-data`, identification to `causal-inference`.

## 3 · `causal-inference` — decide what to adjust for, and how to estimate

- **DAG:** age, comorbidity, baseline labs, and prior care are common causes of treatment choice
  and mortality (confounders → adjust). "Second prescription" and "post-baseline eGFR" are
  consequences of treatment (→ do **not** adjust). Drug→biomarker→death is a mediator (→ do not
  adjust unless decomposing).
- **Adjustment set** (from `dagitty::adjustmentSets`): {age, sex, comorbidity index, baseline
  labs, prior healthcare use}.
- **Positivity/overlap:** estimate the propensity score (P(A | confounders)); inspect overlap by
  arm; trim non-overlapping tails (and note the estimand now refers to the overlap population).
- **Estimator:** IPTW with stabilized weights (estimand = ATE) **or** PS matching (ATT); plan a
  doubly-robust (AIPW) version as the primary for efficiency + protection against one model being
  wrong.

**Hands off** the actual weighting + outcome model to `statistical-analysis`, and missing
confounders to `missing-data` (impute *before* estimating).

## 4 · `missing-data` — handle the 18% missing creatinine honestly

- **Mechanism:** plausibly MAR given measured covariates (sicker patients get labs more often) →
  multiple imputation, not complete-case.
- **Imputation model:** `mice`, m = 20, PMM for labs, **including the outcome and the treatment**
  and auxiliary variables (visit frequency) so MAR is plausible and the analysis stays congenial.
- **Then:** estimate the causal effect *within each imputation* and **pool with Rubin's rules**.
- **Sensitivity:** delta-shift the imputed creatinine for a worst-case MNAR check.

## 5 · `statistical-analysis` — fit the primary model

- Fit the IPTW-weighted Cox model (and an AIPW estimator), within each imputation, with a robust
  sandwich SE; pool across imputations.
- Report the **hazard ratio and 1-year risk difference with 95% CIs**, the number of events, and
  the effective sample size after weighting.
- (R: `WeightIt` + `survey`/`coxph` with robust SE; Python: stabilized weights + `lifelines`.)

## 6 · `method-evaluation` — adversarial critique before anyone believes it

Using `templates/observational_causal.md` + the rubric:

- **Balance:** standardized mean differences after weighting all < 0.1? Extreme weights trimmed?
- **Overlap:** good, after trimming; estimand caveat stated.
- **Unmeasured confounding:** **E-value** computed — an unmeasured confounder would need
  HR ≈ 2.1 with both treatment and death to explain away the effect; plausible? Add a
  **negative-control outcome** (e.g. an outcome neither drug should affect) — null, as hoped.
- **Readiness:** `conditionally_ready` — credible, with the residual-confounding caveat and the
  overlap-population estimand clearly stated. (Had the analysis been the naive unadjusted
  comparison, the rating would be `not_ready` for a causal claim.)

## 7 · `reporting-and-reproducibility` — write it up so it survives review

- **STROBE** checklist; participant-flow cascade matching §2's attrition.
- **Table 1** by treatment arm with **standardized differences** (not p-values), before and after
  weighting.
- **Effect:** "Initiating A vs B was associated with an absolute 1-year mortality difference of
  −2.4% (95% CI −4.1 to −0.6) and HR 0.82 (0.71–0.95), from an IPTW-weighted Cox model adjusted
  for {…}, pooled over 20 imputations. E-value 2.1." Absolute **and** relative effects; correct
  scale labels; causal language justified only by the design + sensitivity analyses.
- **Reproducibility:** seed, `renv.lock`, `sessionInfo()`, a Quarto report that regenerates every
  number, and a data/code availability statement (code public; EHR data restricted, with a
  synthetic dataset provided).

---

## What the suite bought you

Every fatal trap in this question is one a hurried analysis hits: immortal time, adjusting for a
post-treatment variable, dropping the 18% missing, calling an unadjusted association an effect,
and reporting a bare p-value. The orchestrated workflow caught each one *before* it reached the
manuscript — which is the entire point.

> A note on scope: a real comparative-effectiveness study like this warrants a qualified
> biostatistician/epidemiologist. The suite makes the reasoning explicit and the code correct and
> reproducible; it does not replace accountable human review on consequential work.
