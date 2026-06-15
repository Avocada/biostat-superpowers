# Reproducible Project

Target: a colleague (or you, in a year) can clone the project, run one command, and get the same
numbers and figures. Reproducibility is a deliverable, not a courtesy.

## Project structure

```text
project/
├── README.md            how to reproduce: dependencies + the one command to run
├── data/
│   ├── raw/             immutable inputs — never edited (or a script that fetches them)
│   └── processed/       generated; reproducible from raw + code
├── R/  or  src/         analysis code, ordered (00_setup, 01_clean, 02_analyze, 03_report)
├── results/             generated tables, model objects, logs
├── figures/             generated plots
├── report.qmd / .Rmd / .ipynb   the literate document tying it together
├── renv.lock / requirements.txt environment lockfile
└── .gitignore           exclude large/derived data and secrets
```

Never overwrite `data/raw/`. Everything else should be regenerable.

## The reproducibility checklist

1. **Set a seed** for any randomness (imputation, bootstrap, CV, simulation): `set.seed(123)` /
   `np.random.seed(123)` — and record it.
2. **Lock the environment:**
   - R: `renv::init()` → `renv::snapshot()` produces `renv.lock`; `renv::restore()` rebuilds it.
   - Python: a pinned `requirements.txt` (or `uv`/`poetry`/conda env). Note the language version.
3. **Record session info** with the results: `sessionInfo()` (R) / `pip freeze` or
   `session_info` (Python), saved to `results/session_info.txt`.
4. **Use relative paths** and a project root (`here::here()` in R) — no machine-specific absolute
   paths.
5. **Make it literate.** Quarto / R Markdown / Jupyter that runs top-to-bottom and embeds the
   numbers and figures, so the manuscript values come from code, not copy-paste. For pipelines,
   `targets` (R) or a `Makefile` gives a single reproducible build.
6. **One command to reproduce** — document it in the README (e.g. `quarto render report.qmd`,
   `Rscript run_all.R`, `make all`, or `targets::tar_make()`).

## Data and code availability statement

Most journals require one. State where the code lives (a repository + a tagged release or
archived DOI via Zenodo/OSF), and the data-access terms — open, on request, or restricted with
the reason (e.g. patient privacy / IRB). If data cannot be shared, share the code and a synthetic
or simulated dataset that exercises the pipeline.

## Minimal reproducible R skeleton

```r
# run_all.R — reproduce the whole analysis
set.seed(123)
options(stringsAsFactors = FALSE)
dir.create("results", showWarnings = FALSE)

raw <- readr::read_csv("data/raw/input.csv")          # never written back to
# ... clean -> analyze -> save tables/figures to results/ and figures/ ...

writeLines(capture.output(sessionInfo()), "results/session_info.txt")
```

Pair this with `renv.lock` and a README documenting the single command, and the analysis is
reproducible.
