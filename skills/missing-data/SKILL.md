---
name: missing-data
description: >
  Use this skill to handle missing data properly — diagnose the missingness pattern and mechanism
  (MCAR / MAR / MNAR), decide between complete-case analysis and multiple imputation, build and run
  multiple imputation (mice in R, IterativeImputer / statsmodels MICE in Python), pool results with
  Rubin's rules, and run sensitivity analyses for data that may be missing-not-at-random. Use it
  whenever a dataset has non-trivial missing values, when someone asks "should I impute or drop?",
  "how do I do multiple imputation?", "is complete-case okay here?", mentions MICE / MAR / MNAR, or
  when dropout / loss-to-follow-up threatens an analysis.
---

# Missing Data

Missing data is an inference problem, not a data-cleaning chore. Dropping incomplete rows is a
*method* with assumptions — usually stronger and less honest ones than imputing. The goal is a
valid estimate and honest uncertainty under a stated, defensible assumption about *why* data are
missing.

> Profiling the amount and location of missingness lives in `data-understanding-preprocessing`;
> this skill decides the *handling*. Fit the analysis model via `statistical-analysis`, and route
> the "is this approach appropriate?" call to `method-evaluation`.

## Core workflow

1. **Quantify and map the missingness.** Percent missing per variable and per subject; the
   missing-data *pattern* (monotone, as in dropout, vs non-monotone); and which variables are
   missing together. Visualize (e.g. `naniar`/`VIM` in R, `missingno` in Python).
2. **Reason about the mechanism** (you cannot fully test it):
   - **MCAR** — missingness unrelated to any data. Complete-case is unbiased but inefficient.
     (Little's test can *reject* MCAR but cannot prove it.)
   - **MAR** — missingness depends on *observed* data. Multiple imputation and likelihood methods
     are valid. This is the usual working assumption.
   - **MNAR** — missingness depends on the *unobserved* value itself (e.g. sickest patients drop
     out). No method fixes this from the data alone — it requires assumptions and **sensitivity
     analysis**.
3. **Choose a strategy** (map below). Default to **multiple imputation under MAR** for analysis
   variables; use complete-case only when it is defensible (e.g. missingness only in predictors and
   plausibly MCAR, or missingness only in the outcome under MAR given covariates).
4. **Build the imputation model carefully** (see `references/multiple-imputation.md`):
   - Make it **congenial** with (at least as rich as) the analysis model — *include the outcome*
     and any interactions/nonlinearities the analysis uses.
   - Add **auxiliary variables** that predict missingness or the missing values (they make MAR more
     plausible and improve efficiency), even if not in the analysis model.
   - Impute on the correct scale; respect variable types (logistic for binary, PMM for skewed
     continuous), and impute *before* deriving variables consistently ("just another variable" vs
     passive imputation — be deliberate).
5. **Generate m imputations**, **fit the analysis model in each**, and **pool with Rubin's rules**
   (point estimates averaged; variance combines within- and between-imputation components). Use
   more imputations when the fraction of missing information is high (m ≥ the percent missing is a
   reasonable rule of thumb; more is cheap).
6. **Run MNAR sensitivity analysis.** Stress the MAR assumption with a **delta / pattern-mixture**
   shift (impute then shift the missing group's values by a clinically plausible amount) or
   selection models, and report how the conclusion moves. For dropout in longitudinal trials,
   consider reference-based imputation (e.g. jump-to-reference).
7. **Report it** (the missing-data section reviewers look for): amount and pattern of missingness,
   the assumed mechanism and why, the method and software, the imputation model and auxiliary
   variables, m, and the sensitivity-analysis result.

## Strategy map

| Situation | Reasonable approach | Avoid |
|---|---|---|
| Trivial missingness (<~5%), plausibly MCAR | complete-case (note it) | over-engineering |
| Missingness in covariates, MAR | multiple imputation (include outcome) | single mean/median imputation |
| Missing outcome, MAR given covariates | MI, or a likelihood/MMRM model | imputing then treating as observed without pooling |
| Longitudinal dropout | MMRM (MAR) or MI; reference-based for MNAR | LOCF (biased, understates uncertainty) |
| Suspected MNAR | MAR primary + MNAR sensitivity (delta/pattern-mixture) | pretending MAR is verified |

**Do not** use single imputation (mean/median/regression) for the primary analysis — it
understates uncertainty. **Do not** use last-observation-carried-forward as a default. **Do not**
impute the outcome and then analyze imputations as if they were observed without pooling.

## Hand-offs

- Quantifying/locating missingness, structural vs informative missing → `data-understanding-preprocessing`.
- Fitting the analysis model within each imputation → `statistical-analysis`.
- Missing *confounders* in a causal analysis → impute here, then estimate via `causal-inference`.
- "Is this missing-data approach valid?" → `method-evaluation`.
- Reporting the missing-data methods → `reporting-and-reproducibility`.

## Output

Return a **Missing-Data Plan/Report**: (1) missingness amount and pattern, (2) the assumed
mechanism with justification, (3) the chosen strategy and why, (4) the imputation model
(variables, types, auxiliaries, m) or the complete-case justification, (5) pooled results (Rubin's
rules) with CIs, (6) MNAR sensitivity results and how the conclusion moves, (7) the reportable
methods paragraph, (8) open questions.
