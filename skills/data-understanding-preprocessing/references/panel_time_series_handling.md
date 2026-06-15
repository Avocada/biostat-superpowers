# Panel and Time-Series Handling

Use this reference when observations are ordered, repeated by entity, or used for forecasting.

## Structure Detection

- Entity ID: person, account, item, store, device, site, patient, region, or product.
- Time index: timestamp, date, period, sequence number, event order, or snapshot date.
- Panel type: single time series, multiple independent series, balanced panel, unbalanced panel, event history, or irregular observations.
- Target horizon: next step, fixed future window, event within horizon, cumulative outcome, or survival/censoring endpoint.

## Feature Construction Rules

- Lag features must use values strictly before prediction time.
- Rolling windows must exclude future rows and usually exclude the target row when appropriate.
- Cumulative features must be recomputed within each entity and cutoff time.
- Calendar features are allowed only if known at prediction time.
- Time since prior event and observation counts should handle missing history explicitly.
- Aggregates across entities must be fit or computed using training-only historical data when they learn from outcomes.

## Split Strategy

- Forecasting: use chronological validation, rolling-origin validation, or blocked time splits.
- Repeated entities: use group-aware splits when the task is new-entity generalization.
- Same-entity future prediction: allow prior history for the entity but evaluate on later periods only.
- Sparse panels: check whether validation periods contain enough observations per entity.
- Event history: respect censoring and delayed labels.

## Quality Checks

- Duplicate entity-time rows.
- Non-monotonic timestamps within entity.
- Large gaps, irregular intervals, or source outages.
- Entities appearing only in validation or test.
- New categories or IDs after the training cutoff.
- Target leakage through post-period summaries.

## Output Requirements

Specify entity key, time key, prediction time, horizon, allowed history, lag and rolling rules, temporal split dates, and how cold-start entities are handled.
