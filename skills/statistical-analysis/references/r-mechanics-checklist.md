# R Mechanics Checklist

Use this checklist before or during R statistical analysis. It is adapted from the R mechanics topics in *Learning Statistics with R*, Chapter 4: comments, packages, workspace, file paths, loading/saving data, variable classes, factors, data frames, lists, formulas, generic functions, and help.

## 1. Comments and Script Readability

- Write scripts as reproducible analysis records, not console transcripts.
- Use comments to explain analytical intent, not every line of syntax.
- Separate sections clearly: setup, import, audit, cleaning, summaries, modeling, outputs.

```r
# Import raw data and keep it unchanged.
raw <- utils::read.csv(input_file, na.strings = c("", "NA", "N/A"))
dat <- raw
```

## 2. Packages

- Load required packages explicitly with `requireNamespace()` or `library()` near the top of the script.
- Do not assume packages are installed. Report missing packages and install only when the user requests it.
- Prefer explicit namespaces for functions that are common or ambiguous.
- Record package versions for reproducibility when the analysis will be shared.

```r
pkgs <- c("stats", "utils", "graphics")
missing <- pkgs[!vapply(pkgs, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing)) stop("Missing packages: ", paste(missing, collapse = ", "))

sessionInfo()
```

## 3. Workspace Hygiene

- Avoid relying on objects already present in `.GlobalEnv`.
- Create all analysis objects inside the script.
- Use `ls()` only for diagnosis; avoid `rm(list = ls())` in shared scripts unless the user explicitly wants a clean interactive session.
- Name objects by role: `raw`, `dat`, `dat_clean`, `summary_tbl`, `fit`, `diagnostics`.

```r
ls()
str(dat)
```

## 4. File System and Paths

- Inspect the current working directory with `getwd()` when debugging.
- Prefer project-relative paths if the project structure is known.
- Create output directories explicitly.
- Do not overwrite raw input files.
- Use forward slashes in R paths, including on Windows.

```r
getwd()
list.files("data")
dir.create("results", showWarnings = FALSE, recursive = TRUE)
```

## 5. Loading and Saving Data

- Make delimiter, header, encoding, and missing-value strings explicit.
- Keep a raw copy and a cleaned working copy.
- Save cleaned data and derived tables with filenames that describe the analysis stage.
- For R-only objects, use `saveRDS()`/`readRDS()` rather than a whole workspace file when possible.

```r
raw <- utils::read.csv("data/input.csv", na.strings = c("", "NA", "N/A", "null"))
dat <- raw

saveRDS(dat, "results/dat_clean.rds")
utils::write.csv(dat, "results/dat_clean.csv", row.names = FALSE)
```

## 6. Special Values and Classes

- Check for `NA`, `NaN`, `Inf`, and impossible numeric values before summaries or models.
- Inspect classes with `str()`, `class()`, and `vapply(dat, function(x) paste(class(x), collapse = "/"), character(1))` — plain `vapply(dat, class, character(1))` errors on multi-class objects such as `POSIXct`/ordered factors.
- Convert character columns intentionally; do not let accidental coercion drive analysis.
- For numeric conversion, compare missingness before and after conversion.

```r
classes <- vapply(dat, function(x) paste(class(x), collapse = "/"), character(1))  # multi-class safe
missing <- colSums(is.na(dat))
nonfinite_numeric <- vapply(dat, function(x) {
  is.numeric(x) && any(!is.finite(x), na.rm = TRUE)
}, logical(1))
```

## 7. Factors

- Use factors for categorical predictors/groups.
- Set reference levels deliberately for regression or group comparisons.
- Use ordered factors only when the level order is analytically meaningful.
- Check sparse or empty levels after filtering.

```r
dat$group <- factor(dat$group)
dat$group <- stats::relevel(dat$group, ref = "control")
table(dat$group, useNA = "ifany")
```

## 8. Data Frames

- Audit data frames with dimensions, names, classes, head/tail, missingness, and duplicate keys.
- Use `$` for clear single-column access and `[` for programmatic row/column subsets.
- Guard against accidental vector dropping when subsetting one column.

```r
dim(dat)
names(dat)
str(dat)
head(dat)
dat_one_col <- dat[, "age", drop = FALSE]
```

## 9. Lists

- Use lists for grouped outputs, multiple model fits, diagnostics, or audit bundles.
- Name list elements so downstream output is readable.
- Save complex result lists with `saveRDS()`.

```r
results <- list(
  audit = audit,
  summaries = summary_tbl,
  model = fit
)
saveRDS(results, "results/analysis_results.rds")
```

## 10. Formulas

- Build formulas only after confirming variable names exist.
- Keep outcome and predictor definitions explicit.
- Use `stats::as.formula()` for programmatic formulas, and validate with `all.vars()`.
- Remember that formulas carry an environment; avoid hidden dependencies by using `data = dat`.

```r
outcome <- "y"
predictors <- c("group", "age", "sex")
fml <- stats::as.formula(paste(outcome, "~", paste(predictors, collapse = " + ")))
stopifnot(all(all.vars(fml) %in% names(dat)))
fit <- stats::lm(fml, data = dat)
```

## 11. Generic Functions

- Use generic functions like `print()`, `summary()`, `plot()`, and `predict()` after checking object class.
- Save model-specific summaries and diagnostics rather than assuming generic output is sufficient.

```r
class(fit)
summary(fit)
```

## 12. Help and Documentation

- Use `?function`, `help("function")`, `??keyword`, and `help.search("keyword")` for R documentation.
- Inspect argument defaults and return values before using unfamiliar functions in an analysis pipeline.
- Prefer package vignettes or official documentation when a function changes statistical interpretation.

```r
?read.csv
help("lm")
help.search("missing values")
```
