# Statistical Analysis Workflow in R

Use this reference when the user asks for a full R statistical analysis pipeline. The goal is to make data analysis traceable from input file to model-ready output while choosing regression models only when outcome scale, design, and research question support the choice.

## 1. Intake

Capture the minimum analysis contract before writing model code:

- Research question or prediction target.
- Outcome variable and its scale: continuous, binary, count, ordinal, nominal, time-to-event, repeated measure.
- Candidate predictors, grouping variables, covariates, IDs, time variables, and strata.
- Unit of observation and whether rows are independent.
- Required outputs: cleaned data, tables, figures, model summaries, manuscript-ready results.
- Constraints: package style, base R/tidyverse/data.table, privacy, runtime, no internet, no package installation.

If the user provides only a file and asks to analyze it, first build an audit and descriptive pipeline, then ask or state the assumptions needed for inferential modeling.

## 2. Project Layout

Prefer this simple layout unless the repository already has one:

```text
data/       raw or user-provided inputs
results/    generated tables, cleaned data, logs, model objects
figures/    generated plots
scripts/    reusable R scripts
```

Never overwrite files in `data/`. Save generated outputs elsewhere.

## 3. Data Import

Import with explicit assumptions:

- File type and delimiter.
- Header and column-name policy.
- Missing-value strings.
- Character encoding if relevant.
- Whether character columns should stay character until intentional conversion.

Recommended audit after import:

```r
audit <- list(
  n_rows = nrow(dat),
  n_cols = ncol(dat),
  names = names(dat),
  classes = vapply(dat, function(x) paste(class(x), collapse = "/"), character(1)),
  missing = colSums(is.na(dat))
)
```

## 4. Variable Dictionary

Create a table with one row per variable:

- `variable`
- `class`
- `n_missing`
- `n_unique`
- `example_values`
- `role` if known: outcome, predictor, covariate, ID, grouping, time, exclude
- `notes`

Use the dictionary to decide conversions and modeling eligibility.

## 5. Quality Checks

Run checks before summaries or models:

- Duplicate rows or duplicate IDs where IDs are expected unique.
- Missingness by key variables and groups.
- Numeric ranges, impossible values, non-finite values.
- Categorical levels, rare levels, whitespace/case inconsistencies.
- Date parsing and time ordering.
- Group sizes and empty cells for grouped analyses.
- Outcome availability and class.

Report warnings in plain language and save a machine-readable summary table.

## 6. Cleaning Rules

Keep cleaning decisions explicit and reversible:

- Preserve `raw`.
- Create `dat_clean`.
- Record exclusions and recodes.
- Convert factors only after inspecting levels.
- Keep IDs as character unless numeric operations are truly intended.
- Avoid silently dropping missing rows; define a complete-case object only for a named analysis.

```r
model_vars <- c("outcome", "group", "age", "sex")
dat_model <- dat_clean[stats::complete.cases(dat_clean[, model_vars]), model_vars, drop = FALSE]
```

## 7. Descriptive Analysis

Always produce descriptive outputs before fitting models:

- Overall summaries for key numeric variables: mean, SD, median, IQR, min, max, missing.
- Frequency tables for categorical variables.
- Grouped summaries for the main grouping variable.
- Basic plots matched to variable type: histogram/density, boxplot, bar plot, scatterplot.

Keep descriptive summaries separate from inferential claims.

## 8. Model Preparation

Only construct model formulas after confirming:

- Outcome exists and has expected type.
- Predictors exist and have expected type.
- Factors have intended reference levels.
- Missing-data policy is explicit.
- Row independence or repeated-measure structure is addressed.

Formula pattern:

```r
outcome <- "outcome"
predictors <- c("group", "age", "sex")
fml <- stats::as.formula(paste(outcome, "~", paste(predictors, collapse = " + ")))
stopifnot(all(all.vars(fml) %in% names(dat_model)))
```

Model family defaults only when justified by outcome type and design:

- Continuous outcome: linear regression, with diagnostics for residual pattern, nonlinearity, influential points, and heteroskedasticity.
- Binary outcome: logistic regression, with event counts, sparse cells, separation checks, and odds-ratio reporting.
- Count outcome: Poisson regression first, with overdispersion checks before quasi-Poisson, negative binomial, or zero-inflated alternatives.
- Ordinal outcome: proportional odds or ordinal regression when levels are ordered.
- Nominal multiclass outcome: multinomial regression when levels are unordered.
- Time-to-event outcome: Cox regression when follow-up time, event indicator, and censoring are present.
- Repeated or clustered data: mixed models, GEE, or cluster-robust inference; do not ignore non-independent rows.

For detailed model choice and code patterns, read `regression-models.md`. For diagnostics, coefficient tables, and interpretation, read `model-diagnostics-reporting.md`.

## 9. Diagnostics and Sensitivity

For any fitted model, include diagnostics appropriate to the method:

- Sample size used versus imported.
- Dropped rows and missingness reason.
- Coefficient table with confidence intervals and transformed estimates when useful: OR, IRR, HR.
- Residual or assumption checks for linear models.
- Influence/outlier checks when high leverage could matter.
- Sensitivity to factor reference levels, exclusions, or missing-data policy when these choices are consequential.

## 10. Outputs

Save outputs with deterministic filenames:

- `results/variable_dictionary.csv`
- `results/missingness_summary.csv`
- `results/group_summary.csv`
- `results/dat_clean.csv` or `results/dat_clean.rds`
- `results/model_summary.txt` or structured CSV tables
- `results/session_info.txt`
- figures under `figures/`

Include a short run log:

```r
writeLines(capture.output(sessionInfo()), "results/session_info.txt")
```

## 11. Reporting

When returning results to the user:

- State data dimensions and exclusions.
- State variable conversions and missing-data policy.
- Separate descriptive findings from model-based findings.
- Name output files created.
- Flag unresolved assumptions or data problems that could change conclusions.

Do not overclaim causal conclusions from observational data unless the design supports causal inference and the user has specified an identification strategy.
