# Resampling and Simulation Evaluation Template

Use for bootstrap intervals, permutation tests, Monte Carlo studies, simulation-based calibration, power analysis, and resampling validation.

## Specify

- Target statistic, estimand, resampling unit, dependence structure, number of resamples, and interval/test method.
- Whether resampling is used for uncertainty, validation, model selection, or simulation recovery.
- Data-generating process assumptions for simulation.

## Assumptions

- Resampling unit matches the sampling design: row, cluster, block, time series block, subject, or stratified unit.
- Bootstrap distribution approximates the sampling distribution for the statistic.
- Permutation exchangeability holds under the null.
- Simulation data-generating process is plausible for the intended claim.

## Diagnostics

- Bootstrap distribution shape, extreme resamples, convergence by number of resamples.
- Interval stability across seeds and resample counts.
- Coverage, bias, Type I error, power, and calibration in simulation.
- Preservation of clustering, stratification, censoring, or temporal dependence.

## Stress Tests

- Percentile, basic, normal, studentized, and BCa intervals where appropriate.
- Cluster/block bootstrap versus naive row bootstrap.
- Alternative plausible data-generating processes.
- Seed and resample-count stability.
- Small-sample or sparse-event edge cases.

## Compare

- Analytic intervals versus bootstrap intervals.
- Parametric versus nonparametric bootstrap.
- Permutation test versus parametric test for small or distribution-sensitive settings.

## Improve

- Use cluster or block resampling when independence is false.
- Increase resamples if Monte Carlo error is too large.
- Report simulation assumptions and sensitivity instead of a single scenario.
- Use `statistical-analysis` for executable bootstrap, cross-validation, or simulation code.
