---
name: data-understanding-preprocessing
description: >
  Use this skill to inspect, understand, profile, validate, and prepare a dataset BEFORE
  modeling — clinical, epidemiological, EHR/registry, omics, survey, or any tabular/longitudinal
  research data. It produces an analysis-ready data specification: study/estimand interpretation,
  variable roles and types, eligibility and time-zero definition, the analysis table (grain,
  primary key, outcome construction), data-quality and missingness assessment, outlier review,
  a leakage/immortal-time audit, train/validation/test (or internal/external) split design, and
  a reproducible preprocessing pipeline fit on training data only. Use it whenever someone has a
  dataset and a question and asks "is this data ready, and how do I prepare it?"
---

# Data Understanding and Preprocessing

Prepare data so that the analysis that follows is valid by construction. Most analysis errors are
born here — in an undefined cohort, a leaky predictor, an outcome-dependent missingness, or a
time-zero that lets the future leak into the past. This skill catches them before a model is fit.

## Core workflow

1. **Clarify the study objective and estimand.**
   - Identify the outcome, the unit of analysis, the population, the time origin ("time zero"),
     the follow-up window, the exposure/predictors of interest, and whether the goal is
     descriptive, associational, causal, or predictive.
   - If the outcome definition, time zero, or estimand is unresolved, say so and route to
     `study-design-and-power`. Do not preprocess around an undefined target.

2. **Detect data modality.** Tabular (rows = subjects/observations); longitudinal/panel (repeated
   measures per subject, visit structure); time-to-event (follow-up time + event indicator +
   censoring); text (clinical notes); imaging/omics/waveform; or mixed. Plan a per-modality
   pipeline for mixed data.

3. **Profile the dataset.** With local file access, run `scripts/profile_dataset.py` (Python) on a
   CSV; in R, the equivalent is `skimr::skim()` + `summary()` + `dplyr::count()` per categorical.
   Inspect shape, types, missingness, uniqueness, ranges, categorical levels, dates, and
   suspicious values. For type heuristics read `references/data_type_taxonomy.md`.

4. **Assign variable roles.** Mark each variable as outcome, exposure/treatment, confounder,
   identifier, timestamp, grouping/cluster key, stratification key, weight, offset/exposure-time,
   leakage candidate, or exclude. Keep identifiers, timestamps, and cluster keys even when they
   are not model terms — splits and clustering need them.

5. **Infer variable types** (continuous, count, binary, nominal, ordinal, datetime, duration,
   ID-like, constant, high-cardinality, structured string). Do not treat coded categoricals
   (ICD/CPT codes, site IDs) as continuous.

6. **Check data quality.** Duplicate subjects/visits, impossible values (negative age, future
   dates), inconsistent units (mg vs g, mmol/L vs mg/dL), invalid categories, parsing failures,
   class imbalance, and selection artifacts. Flag issues that threaten the *estimand or
   assumptions*, not only predictive performance.

7. **Assess missingness** (per variable and per subject). Distinguish structural/"not applicable"
   missingness, MCAR, MAR, and outcome-dependent (MNAR) missingness. **Do not impute before
   splitting** if imputation learns from the data distribution. For anything beyond trivial
   missingness, route the imputation design to `missing-data`.

8. **Assess outliers and influence.** Univariate extremes, impossible values, influential
   subjects, rare categories, time-local spikes. Decide — with domain plausibility — whether to
   correct, winsorize, transform, model robustly, or leave as-is. Record the decision.

9. **Audit leakage and time.** Read `references/leakage_checklist.md`. In biomedical data the
   classic traps are **time/measurement leakage** (a lab drawn after the outcome), **immortal
   time bias** (defining exposure using post-baseline information), and **target construction
   leakage** (a feature derived from the outcome's defining event). Compare every candidate
   predictor against time zero and the outcome definition.

10. **Specify the analysis table.** Read `references/modeling_table_spec.md`. Define grain,
    primary key, outcome construction, index/time-zero, eligibility rules, the feature
    availability window, joins, final columns, excluded columns, and the output schema.

11. **Define the analysis cohort explicitly.** State inclusion/exclusion criteria and produce the
    attrition counts (a participant-flow / CONSORT-style table): N screened → N eligible →
    N analyzed, with the reason and count at each exclusion. Never drop subjects silently.

12. **Plan the split / validation structure.** Read `references/preprocessing_decision_tree.md`.
    Prefer **time-based** splits when prediction has temporal order; **group/subject-aware** splits
    when rows share a subject, site, or family; **stratified** splits when class balance matters
    and does not violate time/group boundaries. For prognostic models, distinguish internal
    (cross-validation/bootstrap) from **external/temporal/geographic** validation. Name each
    partition's role.

13. **Handle longitudinal / panel / event-history structure.** Read
    `references/panel_time_series_handling.md` for entity ID, time index, horizon, lag rules,
    rolling windows, censoring, gaps, and validation design that respects subject boundaries.

14. **Align preprocessing with the estimand and analysis.** Read
    `references/metric_dependent_preprocessing.md`. Tie outcome transforms, categorization
    (avoid dichotomizing continuous variables without reason), scaling, and class-imbalance
    handling to the planned analysis and the effect measure — not to leaderboard metrics.

15. **Record data provenance and analysis operations.** Read `references/operational_decisions.md`
    for data source/version, extraction date, coding dictionaries, derivation rules, and the
    artifacts you will save. Reproducibility starts with knowing exactly what data you have.

16. **Recommend visualizations.** Outcome distribution / event rate; missingness heatmap and
    missingness-by-group; numeric histograms/box plots; categorical frequencies and rare-category
    tables; time trends and follow-up/censoring plots for longitudinal data; exposure–outcome
    plots appropriate to the variable types.

17. **Build the reproducible preprocessing pipeline.** Fit every learned transform (imputation,
    scaling, encoding, feature selection) **on training data only**, inside a pipeline
    (`recipes`/`tidymodels` in R; `sklearn.Pipeline`/`ColumnTransformer` in Python). Keep a
    manifest of dropped fields and why. Set seeds; assert the schema; save artifacts.

## Constraints

- Do not model before the outcome definition, analysis-table grain, time zero, split strategy,
  and leakage risk are settled.
- Do not fit imputers, scalers, encoders, or selectors on validation/test/external data.
- Do not rely on automatic type inference for identifiers, codes, ordinal fields, dates, or
  leakage-prone variables.
- Do not silently drop rows or columns — record the rule, the count affected, and the rationale.
- Do not dichotomize continuous variables without a pre-specified, defensible reason.
- Keep external/temporal validation data untouched by all fitting and selection.
- Surface uncertainty; ask for domain clarification only when an assumption would materially
  change the analysis.

## Hand-offs

- Undefined estimand/design/sample size → `study-design-and-power`.
- Non-trivial missingness (imputation, MNAR sensitivity) → `missing-data`.
- Confounding / causal adjustment-set decisions → `causal-inference`.
- Fitting and interpreting the model → `statistical-analysis`.
- "Is this preparation appropriate?" critique → `method-evaluation`.

## Output

Return an **Analysis-Ready Data Specification** with: (1) dataset summary, (2) study/estimand
interpretation, (3) data modality, (4) variable roles & inferred types, (5) analysis-table spec,
(6) data-quality findings & quality gates, (7) missingness & outliers, (8) leakage/immortal-time
risks and actions, (9) cohort definition & attrition counts, (10) split/validation strategy,
(11) longitudinal/panel handling, (12) estimand-aligned preprocessing decisions, (13) data
provenance, (14) recommended visualizations, (15) a **column-level action table** (column · role ·
type · availability at time zero · missingness action · outlier action · transform/encoding ·
split/grouping use · leakage status · final action · rationale), and (16) open questions. When you
produce code, keep all learned transforms inside train-only fitting boundaries.
