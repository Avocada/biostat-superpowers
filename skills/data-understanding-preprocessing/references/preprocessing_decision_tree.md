# Preprocessing Decision Tree

Use this decision tree to choose split and preprocessing actions before modeling.

## 1. Define the Problem

- If the outcome is unknown, identify likely outcomes and ask for confirmation.
- If the time origin / prediction time is unknown, derive a plausible one from timestamps and
  state the assumption.
- If the goal is explanation or causal inference, separate preprocessing for statistical validity
  from purely predictive feature engineering, and route adjustment-set decisions to
  `causal-inference`.

## 2. Choose Split Strategy

- If the question is prospective or has temporal order, use a time-based split.
- If rows repeat by person, site, device, household, family, or sample, use a group-aware split so
  the same unit cannot appear in both train and test.
- If both time and groups matter, use a time-based split that keeps future groups or future
  observations out of training; consider grouped temporal validation.
- If classification has rare classes and no time or group constraint, use stratified random splits.
- If data are small, use cross-validation (or the bootstrap) aligned with time, group, or
  stratification constraints.
- If the test set represents a separate external-validation cohort (later time, different site),
  keep it untouched and tune only on training or validation data.

## 3. Handle Missingness

- If missingness is structural, encode the structure explicitly or use separate branches.
- If missing means "not applicable", preserve that meaning rather than using generic imputation.
- If missingness may itself be informative and valid at the time of use, add missingness
  indicators (but see `missing-data` — indicators are not a substitute for proper imputation when
  data are MAR).
- If a column is mostly missing, keep only if the values are important, non-leaky, and available
  at the intended time of use.
- Fit imputation rules only on the training partition. For anything beyond simple imputation,
  route to `missing-data`.

## 4. Handle Numeric Variables

- If units are inconsistent, standardize units before modeling.
- If values are impossible, correct from source rules or set to missing with an audit count.
- If values are plausible but extreme, prefer robust models, transformations, winsorization, or
  sensitivity analysis.
- If a model requires scale comparability, standardize or normalize after splitting.
- If a distribution is skewed and positive, consider log1p or Box-Cox style transforms — but do
  not transform an outcome whose effect measure you need to report on the original scale without a
  plan to back-transform.

## 5. Handle Categorical Variables

- If labels differ only by case, whitespace, spelling, or synonyms, normalize categories.
- If categories are rare, group rare levels using a training-only frequency threshold.
- If cardinality is low, use one-hot / indicator coding.
- If cardinality is high, consider hierarchy extraction (e.g. ICD chapters), hashing, embeddings,
  or target encoding with cross-fitting.
- If categories are ordinal, preserve order only when the order is known and meaningful.

## 6. Handle Datetime and Temporal Data

- If timestamps define the outcome after time zero, do not use them as features.
- If using lag or rolling features, compute each row from prior observations only.
- If seasonality matters, create calendar features available at the time of use.
- If sampling is irregular, create elapsed-time, gap, or observation-count features.
- If censoring exists, document the observation window and route time-to-event handling to
  `statistical-analysis`.

## 7. Handle Text and Mixed Data

- If text contains labels, notes written after the outcome, or outcome summaries, treat as leakage.
- If text is valid, choose vectorization based on sample size and model class.
- If text fields are short codes or tags, parse as categorical or multi-label fields.
- For mixed modality, build separate preprocessing branches and combine features only after
  train-only fitting.

## 8. Drop, Keep, or Quarantine

- Drop constants, duplicate columns, invalid identifiers, and confirmed leakage.
- Keep metadata needed for splitting, grouping, auditing, or joining even if excluded from model
  terms.
- Quarantine suspicious variables until domain confirmation.
- Record every exclusion with a reason and a count.

## 9. Build Pipeline

- Split first when feasible.
- Fit preprocessing only on training data.
- Apply identical learned transformations to validation, test, and any future data.
- Version the column schema, role decisions, cleaning rules, and random seeds.
- Add tests or assertions for required columns, type expectations, valid ranges, and category
  handling.
