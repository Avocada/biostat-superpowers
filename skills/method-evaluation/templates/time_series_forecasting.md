# Time Series and Forecasting Evaluation Template

Use for ARIMA, state-space, exponential smoothing, dynamic regression, panel forecasting, rolling-origin validation, and temporal prediction.

## Specify

- Series unit, timestamp, frequency, horizon, forecast origin, and target definition.
- Single series, multiple independent series, panel, intermittent demand, or event history.
- Exogenous variables and their availability at forecast time.
- Evaluation metric and operational forecast cadence.

## Assumptions

- Time ordering is preserved in feature construction, scaling, tuning, and validation.
- Residuals are adequately modeled after trend, seasonality, and autocorrelation structure.
- Exogenous regressors are known or forecastable at prediction time.
- Training period is representative enough for deployment or regimes are handled.
- Horizon-specific performance is evaluated when horizons differ.

## Diagnostics

- Time plots, missing periods, duplicated timestamps, gaps, and level shifts.
- Residual ACF/PACF and whiteness checks.
- Forecast errors by horizon, season, regime, and series.
- Backtesting performance across rolling origins.
- Prediction interval coverage when intervals are reported.

## Stress Tests

- Rolling-origin or blocked time validation.
- Leave-one-period, leave-one-season, or leave-one-regime sensitivity.
- Shock periods, holidays, source outages, and structural break checks.
- Alternative seasonal/trend specifications.
- Exogenous-regressor availability and lag sensitivity.

## Compare

- Naive, seasonal naive, and rolling mean baselines.
- Simple exponential smoothing or ARIMA-style statistical baseline.
- Dynamic regression or machine learning models only under identical temporal validation.
- Compare horizon-specific and aggregate metrics.

## Improve

- Add seasonal terms, differencing, transformations, or state-space components when diagnostics support them.
- Use hierarchical or pooled models for sparse panels.
- Use prediction intervals and coverage checks for uncertainty-sensitive decisions.
- Separate model selection backtests from final temporal holdout.
