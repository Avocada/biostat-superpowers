# Data Type Taxonomy

Use this taxonomy to distinguish statistical meaning from storage format.

## Variable Roles

- Target: outcome to predict or explain.
- Feature: valid input available at prediction time.
- Identifier: row, person, encounter, account, device, site, or transaction key.
- Timestamp: event time, observation time, extraction time, or prediction time anchor.
- Grouping key: entity used for clustered data, repeated measures, group splits, mixed models, or fixed effects.
- Stratification key: variable used to preserve distribution in splits or sampling.
- Weight: sampling, survey, frequency, or inverse-probability weight.
- Offset or exposure: known scale term for count or rate models.
- Leakage candidate: variable that may encode the target, future information, or post-outcome behavior.
- Exclude: field unsuitable for modeling due to quality, leakage, redundancy, or irrelevance.

## Statistical Types

### Numeric Continuous

Measurements on a meaningful numeric scale, such as age, income, lab value, price, height, temperature, or probability score.

Typical preprocessing:
- Validate units and impossible ranges.
- Impute deliberately: multiple imputation for inferential analyses (see `missing-data`); single
  mean/median imputation only inside a prediction pipeline (fit on training folds) or for
  description — alone it understates uncertainty.
- Scale for distance-based or regularized models.
- Transform skewed positive variables with log or power transforms when appropriate.

### Numeric Discrete or Count

Integer-valued quantities such as visits, purchases, events, days, words, or defects.

Typical preprocessing:
- Check for impossible negative values.
- Consider rate construction with exposure.
- Consider log1p or count models for skewed counts.

### Binary

Two-state variables encoded as true/false, yes/no, 0/1, present/absent, or two categories.

Typical preprocessing:
- Normalize inconsistent labels.
- Preserve as binary indicator.
- Verify whether missing is an informative third state or true unknown.

### Nominal Categorical

Unordered labels such as region, diagnosis group, product type, channel, or vendor.

Typical preprocessing:
- Clean spelling, case, whitespace, and synonyms.
- Collapse rare categories when needed.
- Use one-hot, target encoding with strict cross-fitting, hashing, embeddings, or model-native categorical handling.

### Ordinal Categorical

Ordered labels such as low/medium/high, education level, severity grade, Likert scale, or stage.

Typical preprocessing:
- Confirm order with domain context.
- Map to ordered integers only when equal spacing is defensible or model supports monotonic interpretation.
- Otherwise use categorical encoding while preserving order metadata.

### Datetime

Date, time, timestamp, period, or calendar fields.

Typical preprocessing:
- Parse with timezone awareness when relevant.
- Extract calendar features only if available at prediction time.
- Use lags, rolling windows, recency, seasonality, and elapsed time features for temporal tasks.
- Avoid deriving features from future timestamps.

### Duration

Elapsed time between two events, age at event, tenure, length of stay, or time since prior event.

Typical preprocessing:
- Verify endpoints and censoring.
- Ensure both endpoints are available by prediction time.
- Consider log transforms for skewed durations.

### Text

Free-form notes, descriptions, messages, names, comments, or documents.

Typical preprocessing:
- Clean encoding and obvious artifacts.
- Use bag-of-words, TF-IDF, embeddings, topic models, or domain-specific parsers.
- Check for direct target mentions, future documentation, or labels embedded in text.

### ID-like or Code-like

High-cardinality strings or numbers used as keys, product codes, ZIP codes, diagnosis codes, account numbers, or record IDs.

Typical preprocessing:
- Do not treat numeric codes as continuous.
- Use for joins, grouping, blocking, or split control.
- Encode only when the code is meaningful and valid in the target population.
- Consider hierarchy extraction for structured codes.

### Constant or Near-Constant

Variables with one value or very low variance.

Typical preprocessing:
- Drop after verifying they are not indicators of data source, cohort, or extraction process.

### Structured Strings

Fields containing parsable structure such as JSON snippets, comma-separated tags, version strings, URLs, addresses, or compound codes.

Typical preprocessing:
- Parse into components with explicit rules.
- Validate parse failure rates.
- Keep raw field only if downstream model can use it safely.

## Inference Heuristics

- Low unique count alone does not prove categorical type.
- Numeric storage does not prove continuous type.
- High cardinality plus uniqueness ratio near one suggests ID-like behavior.
- Date-like names and parseable date strings should be treated as datetime candidates.
- Columns ending in `_id`, `id`, `uuid`, `key`, `code`, or `number` need role review.
- Columns containing `target`, `label`, `outcome`, `status`, `result`, `score`, `flag`, `future`, `after`, or `post` need leakage review.
- Free-text columns often have high average string length and many unique values.
