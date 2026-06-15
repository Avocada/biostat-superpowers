---
name: method-evaluation
description: >
  Use this skill to critique, evaluate, compare, or improve a statistical method, study design,
  model choice, diagnostic plan, robustness check, validation strategy, or statistical report —
  the adversarial reviewer. It owns the critical-reasoning layer: assumptions, diagnostics,
  stress tests, fair comparison, pros/cons, improvement advice, a readiness rating, and a
  structured evaluation report. Use it when someone asks "is this method appropriate?", "what
  assumptions does this make?", "how could this analysis be wrong?", "how do I compare these
  models fairly?", "review my statistical approach", or before any analysis is reported as final.
---

# Method Evaluation

Evaluate whether a proposed or fitted analysis is appropriate and trustworthy — *without* taking
over data prep or implementation. Your stance is constructive but adversarial: assume the analysis
could be wrong and look for the way it fails before it reaches a journal or a decision.

Ground evaluations in established practice (Harrell, *Regression Modeling Strategies*; Hernán &
Robins, *Causal Inference*; van Buuren, *Flexible Imputation*; Gelman/Hill/Vehtari;
Hastie/Tibshirani/Friedman; Box/Hunter; the relevant reporting guidelines). Use them to drive the
checklist and diagnostics — not as proof by authority.

## Run the critique in a fresh context (use a sub-agent)

The strongest review comes from **fresh eyes that did not produce the analysis.** The agent that
built a model is anchored on its own choices and tends to rationalize them. So whenever the
platform supports it, **dispatch the evaluation to a separate-context sub-agent** (Claude's `Task`
sub-agents, Codex's `task`, or simply a second agent/session) and give it only the *artifacts* —
the data contract, the model spec, the results — not your reasoning for them. Tell it to **try to
break the analysis**.

- Prefer a **different model or a fresh session** for the reviewer than the one that did the work.
- Hand over **what was done, not why** — make the reviewer reconstruct the justification (or fail to).
- For high-stakes claims, run **several independent reviewers** and keep a finding only if a
  majority cannot dismiss it (adversarial verification).
- If no sub-agent mechanism exists, still adopt a deliberately fresh, adversarial stance: re-derive
  the assumptions from scratch and argue the analysis is *wrong* before concluding it is sound.

Independent-context review is not optional polish — it measurably catches problems that
same-context self-review rationalizes away.

## Relationship to the other skills

- Data quality, leakage, missingness adjudication → `data-understanding-preprocessing` / `missing-data`.
- Estimand / design / power questions → `study-design-and-power`.
- Causal identification (DAGs, adjustment sets, overlap) → `causal-inference`.
- Executable fitting, diagnostics, bootstrap, validation code → `statistical-analysis`.
- This skill owns critique: assumptions, diagnostic design, stress-test planning, robustness,
  comparison, improvement, and the final evaluation report. Refer work back to the owner rather
  than duplicating it.

## Core workflow: Specify → Fit/Describe → Diagnose → Stress Test → Compare → Improve → Report

1. **Specify the target and estimand.** Research question or prediction target, outcome scale,
   unit of analysis, sampling/design, time horizon, clustering, and intended use. Identify the
   method family, objective, estimand, performance metric, and whether the goal is causal,
   predictive, descriptive, forecasting, or uncertainty quantification. Route unresolved data or
   design questions to the owning skill.
2. **Fit or describe the method.** If a model was fit, summarize exactly what: formula, features,
   link/loss, tuning, training data, validation scheme, missing-data policy, weighting, software.
   If nothing was fit, produce an *evaluation plan* — do not pretend results exist.
3. **Diagnose assumptions and failure modes.** Name method, design, data, validation, and
   interpretation assumptions. Use the matching file in `templates/`. Distinguish **fatal**
   violations from **repairable** weaknesses from **routine** limitations.
4. **Stress test robustness.** Read `references/stress_tests.yaml`. Plan sensitivity to influential
   observations, missing-data policy, feature/covariate choices, transformations, validation
   split, tuning, clustering, time ordering, unmeasured confounding, and distribution shift. Keep
   final holdout / external data out of all selection.
5. **Compare methods.** Against a null/clinical/simple baseline before complex alternatives. Fair
   comparison: same outcome, same eligible rows (or documented differences), same data-availability
   rules, compatible validation. AIC/BIC only for compatible likelihood models; CV/holdout for
   prediction; do not compare on test data after selection.
6. **Improve.** Recommend simplification, respecification, robust methods, transformations, splines,
   interactions, offsets, cluster handling, calibration, bootstrap intervals, or added checks.
   Separate fixes that need preprocessing from those that need implementation, and name the owner.
7. **Report.** Use `schemas/evaluation_report.schema.json` for the machine-readable structure,
   `references/rubric.md` to grade readiness and severity, and `prompts/report_generator.md` to
   draft the user-facing report.

## Template map (method family → file)

- Linear/logistic/count/ordinal/survival/mixed/clustered regression → `templates/regression.md`
- Classification, regression prediction, regularization, trees, calibration, prognostic models → `templates/machine_learning_prediction.md`
- Forecasting, ARIMA/state-space, autocorrelation, seasonality, backtesting → `templates/time_series_forecasting.md`
- Randomized experiments, factorial/blocked designs, replication → `templates/experiments.md`
- Observational comparisons, confounding, propensity scores, matching, weighting, DiD/IV/RD, unmeasured-confounding sensitivity → `templates/observational_causal.md` (and hand identification to `causal-inference`)
- Bootstrap, permutation, simulation, small-sample inference, resampling validation → `templates/resampling_simulation.md`

For worked, cross-skill examples see `examples/collaboration_workflows.md`.

## Operating rules

- Do not fit models, generate analysis scripts, or run diagnostics here — route implementation to
  `statistical-analysis`.
- Do not adjudicate raw-data quality, leakage, or imputation here — route to
  `data-understanding-preprocessing` / `missing-data`.
- Do not recommend complex models before the baseline and validation design are specified.
- Do not treat predictive accuracy as causal evidence.
- Do not compare models on test-set performance after model selection.
- Do not hide unresolved assumptions — mark them as open questions or required checks.
- Prefer clear, actionable critique over textbook summaries.
- **Pair every finding with an action** — a concrete next step (or "hand this to a statistician")
  for each issue, not just the diagnosis; a non-statistician needs to know what to *do* next.
- **Tier severity** (fatal / serious / routine, or the rubric's critical/high/medium/low) so a
  non-expert can tell what *must* be fixed before submitting.
- **When you ask the user a question, state the consequence of each answer** — what breaks if it is
  answered the wrong way — so the question is actionable, not a cliff edge.

## Output

Return a **Statistical Method Evaluation Report**: (1) evaluation scope, (2) method summary,
(3) assumptions & required evidence, (4) diagnostic plan, (5) stress-test plan, (6) comparison
plan/results, (7) strengths, (8) limitations & risks (with severity), (9) recommended improvements
(with owner & priority), (10) integration hand-off, (11) readiness rating (per `references/rubric.md`),
(12) open questions. Keep it conformant to `schemas/evaluation_report.schema.json` when a structured
report is requested.
