---
name: statistical-analysis
description: >
  Use this skill to fit and interpret a statistical model on prepared data, in R or Python, and
  to produce a reproducible analysis script. It chooses the regression family from the outcome
  scale and study design — linear, logistic, Poisson/negative-binomial, ordinal, multinomial,
  Cox/survival, mixed-effects, and GEE — then runs the right diagnostics, extracts effect
  estimates with confidence intervals (OR/IRR/HR on the correct scale), and adds sensitivity
  checks. Use it when someone says "fit a model", "run the regression", "analyze this in R/Python",
  "which model fits this outcome", "interpret these coefficients", or "debug my model code".
---

# Statistical Analysis

Turn a defined question and a prepared dataset into a defensible, reproducible model. Prefer an
executable script (R or Python) over console-only steps. Fit the **simplest model the design
justifies**, interpret it on the correct scale, and check the assumptions you rely on.

> This skill *implements*. If the estimand, cohort, leakage, or split is unsettled, get them from
> `data-understanding-preprocessing` first. If the question is causal and observational, fix the
> adjustment set with `causal-inference` before fitting. For non-trivial missingness, route to
> `missing-data`. To judge whether the finished analysis is trustworthy, use `method-evaluation`.

## Core workflow

1. **Confirm the analysis contract.** Outcome and its scale (continuous / binary / count / ordinal
   / nominal / time-to-event / repeated measure); the primary exposure and pre-specified
   covariates; the unit of observation and whether rows are independent (clustering, repeated
   measures, matching); offset/exposure time for rates; censoring for time-to-event; and whether
   the goal is inference or prediction.
2. **Establish session hygiene & reproducibility.** Record language and package versions
   (`sessionInfo()` / `pip freeze`), set a seed, use explicit paths, never overwrite raw data, and
   name objects by analysis role. (R details: `references/r-mechanics-checklist.md`.)
3. **Import and audit** before modeling: dimensions, types, missingness, duplicates, group sizes,
   ranges, factor/category levels, date parsing. (Workflow: `references/stat-analysis-workflow.md`.)
4. **Describe before you model.** Outcome distribution / event rate, grouped summaries, and plots
   matched to variable type. Keep descriptive output separate from inferential claims.
5. **Choose the family** from outcome scale, design, dependence structure, censoring, and goal
   (map below). State the choice and why.
6. **Fit the primary model**, then run family-specific diagnostics, extract coefficients with CIs
   and the transformed effect (OR/IRR/HR) where useful, and run pre-specified sensitivity checks.
   (Choice + code: `references/regression-models.md` (R) and `references/python-models.md` (Python).
   Diagnostics, interpretation, and tables: `references/model-diagnostics-reporting.md`.)
7. **Save outputs reproducibly:** cleaned data, coefficient tables, figures, the model object if
   useful, and a run log of inputs, assumptions, diagnostics, and warnings.

## Regression model map (biomedical defaults)

| Outcome / design | Default model | Effect measure | Watch for |
|---|---|---|---|
| Continuous | linear model (`lm` / OLS) | mean difference / slope | nonlinearity, heteroskedasticity, influence; splines/robust SE if needed |
| Binary | logistic (`glm` binomial / `Logit`) | **odds ratio** | events-per-variable, separation, sparse cells; OR ≠ RR |
| Binary, RR wanted | log-binomial or Poisson-with-robust-SE | **risk ratio** | convergence; use modified Poisson if log-binomial fails |
| Count / rate | Poisson, then negative binomial | **incidence-rate ratio** | overdispersion; include `offset(log(person_time))` for rates |
| Ordinal | proportional-odds (`polr` / `OrderedModel`) | odds ratio | proportional-odds assumption |
| Nominal (>2 unordered) | multinomial | relative-risk ratio | don't impose order |
| Time-to-event | Cox (`coxph` / lifelines) | **hazard ratio** | PH assumption, events-per-variable, censoring/time-origin; with competing events define the estimand first (cause-specific Cox vs cumulative-incidence / Fine–Gray) |
| Repeated / clustered / longitudinal | mixed-effects or GEE | conditional vs population-average | justify random-effects structure; convergence/singular fits |

**First-class biomedical concerns:** survival outcomes (Cox, Kaplan–Meier, proportional-hazards
checks, competing risks), longitudinal/clustered data (random effects vs GEE; do not treat
repeated measures as independent), and effect-measure discipline (never relabel an OR as an RR or
an HR as an RR).

## Operating rules

- **Do not pick the model from file names.** Infer only from observed variable structure, design,
  and the stated question.
- **One justified primary model** beats many unexplained ones. Secondary models are diagnostics,
  sensitivity checks, or explicitly requested comparisons — labeled as such.
- **Interpretation is model-specific:** slopes (linear), odds ratios (logistic), incidence-rate
  ratios (Poisson-like), hazard ratios (Cox), conditional effects (mixed models).
- **Associational by default.** Do not use causal language unless a design and identification
  strategy support it (and if so, the adjustment set comes from `causal-inference`).
- **Report uncertainty.** Effect sizes with confidence intervals; p-values are context. Report n,
  events, and rows excluded with the reason.
- **Preserve raw data.** Write derived/cleaned outputs to a separate path.
- **R or Python by fit and context.** Match the project's existing stack; if unspecified, R is the
  biomedical default but Python (`statsmodels` / `lifelines`) is fully supported — see
  `references/python-models.md`. If the runtime is unavailable, still produce the code and say
  execution was not verified here.

## Hand-offs

- Unsettled estimand / cohort / leakage / split → `data-understanding-preprocessing`.
- Observational causal question (adjustment set, estimator) → `causal-inference`.
- Non-trivial missingness (multiple imputation, pooling) → `missing-data`.
- "Is this analysis appropriate and trustworthy?" → `method-evaluation`.
- Table 1, effect-size reporting, reproducible writeup → `reporting-and-reproducibility`.

## Output

Return: (1) the analysis contract and model choice with rationale; (2) the reproducible script
(R or Python); (3) the coefficient/effect table with CIs on the correct scale, plus n and events;
(4) diagnostics and what they imply; (5) sensitivity results; (6) a plain-language interpretation
that names the effect scale and stays within what the design supports; (7) files produced and
open questions.
