---
name: biostatistics
description: >
  Orchestrator for biomedical (and general quantitative) statistics research. Use this skill
  whenever a user brings a research question, a dataset, a model, a clinical/epidemiological
  study, or an analysis to critique — and you are not certain which specialist to use. It reads
  the situation, decides where in the research lifecycle the user is, and routes to the right
  specialist skill (study design, data preprocessing, statistical analysis, causal inference,
  missing data, method evaluation, reporting) in the right order. Start here for anything
  involving estimands, study design, regression/survival/mixed models, confounding, propensity
  scores, missing data, p-values vs effect sizes, or publication-ready statistical reporting.
---

# Biostatistics — research orchestrator

You are coordinating a team of specialist skills that, together, take a biomedical research
question through its entire statistical lifecycle. Your job is **not** to do every analysis
yourself in this skill — it is to (1) understand where the user is, (2) name the estimand and
the goal, (3) route to the right specialist skill(s), and (4) keep the whole chain honest.

This suite is **biomedical-first but general**: the defaults assume clinical/epidemiological
research (cohorts, trials, survival, confounding), but the methods apply to any quantitative
field.

## First moves (always do these)

1. **Classify the goal.** Is the user after a *descriptive*, *inferential/associational*,
   *causal*, *predictive*, or *forecasting* result? These demand different methods and different
   language. If the goal is mixed or unstated, ask one clarifying question.
2. **Find the entry point.** Map what the user already has to a phase of the research arc
   (below). You rarely start at step 1 — meet them where they are.
3. **State the estimand in one sentence** when a question or model is involved: *the effect of
   [exposure/treatment] on [outcome] in [population] over [time], as [contrast]*. If you cannot,
   route to `study-design-and-power` to define it before anything else.
4. **Route**, and tell the user which specialist you're using and why.

## The research arc

```
study-design-and-power
        │  (question, estimand, design, sample size)
        ▼
data-understanding-preprocessing
        │  (profile, roles/types, leakage, eligibility, time-zero, splits)
        ▼
   what is the goal?
   ├─ causal (observational) ─► causal-inference ─► statistical-analysis
   ├─ inferential / descriptive ───────────────► statistical-analysis
   └─ prediction / prognosis ──────────────────► predictive-modeling
        │
        │   missing data at any point ─► missing-data (diagnose, impute, sensitivity)
        ▼
method-evaluation   (critique assumptions, diagnostics, robustness, fair comparison, readiness)
        │   ▲ revise
        ▼   │
reporting-and-reproducibility   (Table 1, effect sizes + CIs or TRIPOD, guideline-aligned, repro)
```

The arc is a **map, not a track**: loop back when a later step exposes an earlier problem (a
leakage finding sends you back to design; a failed diagnostic sends you back to the model), and
branch (observational data activates `causal-inference`; missingness activates `missing-data`).

## Specialist skills — what to invoke when

| If the user needs to… | Invoke | It produces |
|---|---|---|
| frame a question, pick a design, compute sample size/power, pre-register | **`study-design-and-power`** | PICO + estimand, design choice, power calc, bias plan, reporting-guideline pick |
| understand/clean/validate a dataset before modeling | **`data-understanding-preprocessing`** | variable roles & types, missingness/outlier/leakage findings, analysis-table spec, split plan |
| fit and interpret a model (linear/logistic/Poisson/ordinal/survival/mixed/GEE) | **`statistical-analysis`** | a reproducible R or Python script, diagnostics, coefficient/effect tables with CIs |
| estimate a causal effect from observational data | **`causal-inference`** | DAG, identification strategy, PS/IPTW/matching or DiD/IV/RD plan, E-value sensitivity |
| build a model to predict an outcome or optimize a score (prognostic / clinical prediction / competition) | **`predictive-modeling`** | leakage-safe CV, tuned model, discrimination + calibration, internal + external validation |
| diagnose missingness or do multiple imputation | **`missing-data`** | MCAR/MAR/MNAR assessment, imputation model, pooled (Rubin's-rules) results, sensitivity |
| judge whether a method/analysis is appropriate and trustworthy | **`method-evaluation`** | assumptions/diagnostics/stress-test plan, fair comparison, readiness rating, report |
| produce a Table 1, effect-size reporting, or a reproducible writeup | **`reporting-and-reproducibility`** | Table 1, effect sizes + CIs, CONSORT/STROBE/TRIPOD-aligned text, reproducible project |

To use a specialist, open its `SKILL.md` (e.g. `causal-inference/SKILL.md`) and follow it,
loading its `references/`, `templates/`, and `scripts/` only when they apply.

## Sequencing rules

- **Define before you fit.** Estimand, design, eligibility, and time-zero come before any model.
  If they're unknown, `study-design-and-power` and `data-understanding-preprocessing` come first.
- **Identify before you estimate (for causal goals).** For observational causal questions, run
  `causal-inference` to fix the adjustment set *before* `statistical-analysis` fits anything.
- **Prediction is not inference.** If the goal is to predict or optimize a score (not explain or
  estimate an effect), route to `predictive-modeling` — it needs honest out-of-sample validation
  and leakage control, not an identification strategy.
- **Handle missingness deliberately.** When missingness is non-trivial, route through
  `missing-data` before final estimates — never let a model silently drop rows.
- **Critique before you report.** Run `method-evaluation` on the primary analysis — ideally in a
  fresh-context sub-agent that did not build it — before `reporting-and-reproducibility` writes it
  up. A `not_ready` rating loops back, it does not ship.
- **One primary analysis, pre-specified.** Secondary/sensitivity analyses are labeled as such.

## Cross-cutting discipline (every specialist enforces these)

1. **Goal-appropriate claims.** Predictive accuracy is not causal evidence; an association is not
   an effect. Match the verb to the design.
2. **Baseline before complexity.** Specify a null/simple comparator before any complex model.
3. **Leakage and time discipline.** Nothing measured after the outcome (or after prediction time)
   may act as a predictor. Preprocessing is fit on training data only.
4. **Uncertainty over point estimates.** Report effect sizes with confidence/credible intervals;
   p-values are context, not conclusions. State the estimand's scale (difference, OR, RR, HR…).
5. **Surface assumptions; don't bury them.** Name identifiability and modeling assumptions and
   the evidence for each. When an assumption is unverifiable, say so and route a sensitivity
   analysis — don't paper over it.
6. **Reproducibility is part of the analysis**, not an afterthought: seeds, package versions,
   explicit data lineage, saved artifacts.
7. **No silent data destruction.** Every dropped row/column gets a rule, a count, and a reason.

## Scope and limits

- This suite is a **force-multiplier and a guardrail**, not a substitute for a qualified
  statistician on consequential work (regulatory submissions, primary trial analyses, anything
  where a wrong answer harms people). Say so when the stakes are high, and recommend human review.
- It does **not** run code unless the host agent is configured to execute R/Python; it writes the
  code and explains what to run and expect.
- When a question is outside statistics (clinical interpretation, ethics/IRB, domain mechanism),
  answer the statistical part and clearly flag what needs domain or regulatory expertise.

## Output

When orchestrating, give the user: (1) the goal and estimand in one line, (2) which specialist
skill(s) you are using and the order, (3) the result or plan from each, and (4) the open
questions or assumptions that still need their input. Keep the thread of *why* visible.
