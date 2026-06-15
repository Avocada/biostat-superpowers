# Analysis Table Specification

Use this reference to convert dataset understanding into a build-ready analysis-table contract:
the precise, reproducible definition of the rectangle of data the analysis will run on.

## Required Decisions

- **Grain:** define exactly what one row represents (one subject? one subject-visit? one
  person-period?).
- **Primary key:** identify the unique row key, or define how one will be constructed.
- **Outcome:** define the outcome column, any transformation, the outcome/label window, the
  positive class or event definition, censoring rules, and invalid-outcome handling.
- **Time zero / index:** define the timestamp at which follow-up begins and at which covariates
  must be known. This is the anchor that prevents immortal-time and look-ahead bias.
- **Covariate window:** define historical lookback windows and aggregation cutoffs relative to
  time zero.
- **Eligibility:** define which subjects, dates, events, or cohorts are included or excluded, in
  order, with counts.
- **Joins:** define source tables, join keys, join type, expected cardinality, and the allowed
  time direction (no future information joined onto a time-zero row).
- **Split columns:** preserve time, group/cluster, stratification, and subject/linkage ID fields
  even if excluded from model terms.
- **Output schema:** define the final covariate columns, the outcome (and event/time for
  survival), weights, offsets/exposure, cluster IDs, and subject IDs.

## Checklist

- Is the row grain stable and non-duplicated?
- Does every covariate exist at or before time zero?
- Are outcome-construction fields excluded from the covariates?
- Are many-to-one and one-to-many joins audited for row multiplication?
- Are repeated subjects handled with group-aware or longitudinal methods?
- Are train, validation, and test schemas identical except for outcome availability?
- Are all dropped columns and excluded subjects recorded with a reason and a count?

## Column Action Table Fields

Include these fields in the final specification:

- `column`
- `source`
- `role`
- `inferred_type`
- `final_type`
- `available_at_time_zero`
- `missingness_action`
- `outlier_action`
- `encoding_or_transform`
- `split_or_grouping_use`
- `leakage_status`
- `final_action`
- `rationale`

## Common Failure Modes

- Building features from the full dataset before splitting.
- Using a row grain that changes across cohorts or over time.
- Joining future aggregates onto time-zero rows (look-ahead / immortal-time bias).
- Dropping IDs needed for linkage, grouping, tracing, or attrition accounting.
- Letting outcome-missing rows influence preprocessing fit on the training data.
