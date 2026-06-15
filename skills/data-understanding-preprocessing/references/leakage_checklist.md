# Leakage Checklist

Use this checklist before feature engineering and again before model evaluation.

## Prediction-Time Leakage

- Is the feature known at the moment a prediction would be made?
- Was the feature recorded after the target event?
- Does the feature include future measurements, outcomes, dispositions, billing completion, labels, reviews, or manual adjudication?
- Does a timestamp reveal that the row was included only after the outcome occurred?

## Target Construction Leakage

- Was the target derived from columns also present as features?
- Does a feature duplicate, transform, summarize, or threshold the target?
- Does the feature use the same diagnosis, event, transaction, score, status, or result used to define the label?
- Are negative controls or exclusion criteria still present as features?

## Split Leakage

- Can the same person, account, site, product, device, document, or event appear in both train and test?
- Are near-duplicates or repeated observations split across partitions?
- Were imputers, scalers, encoders, feature selectors, text vectorizers, rare-category rules, or target encoders fit before the split?
- Were hyperparameters chosen after looking at test performance?

## Temporal Leakage

- Do rolling, cumulative, or aggregate features include the current or future target window?
- Are calendar features valid for the deployment date?
- Are labels delayed, revised, or backfilled after prediction time?
- Does random splitting let the model train on future behavior and test on the past?

## Aggregation Leakage

- Were group-level statistics computed using validation or test rows?
- Were target rates computed without cross-fitting or nested folds?
- Do global encodings include information from the test distribution?
- Are cohort-level features calculated from a full extract that would not exist in production?

## Proxy Leakage

- Does the feature strongly imply the outcome through workflow artifacts?
- Examples: treatment after diagnosis, cancellation reason after churn, collection status after default, discharge disposition during admission, claim paid amount after adjudication.
- Does missingness itself occur only after the outcome or due to outcome-dependent processes?

## External Data Leakage

- Does joined data include revisions, future snapshots, or publication dates after prediction time?
- Are lookup tables versioned as they would be at deployment?
- Are labels or outcomes embedded in external IDs, filenames, folders, URLs, or notes?

## Actions

- Remove confirmed leakage.
- Lag or window features so only historical information is used.
- Recompute aggregates inside training folds.
- Use group-aware or time-aware splitting.
- Quarantine uncertain variables and ask for domain confirmation.
- Document each leakage decision with feature name, risk, action, and rationale.
