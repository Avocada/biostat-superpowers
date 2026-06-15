---
name: reporting-and-reproducibility
description: >
  Use this skill to turn a finished analysis into a publication-ready, reproducible report:
  building Table 1 (baseline characteristics), reporting effect sizes with confidence intervals
  (not bare p-values), following the right reporting guideline (CONSORT, STROBE, TRIPOD, PRISMA,
  STARD, SPIRIT), drawing participant-flow diagrams, and packaging the analysis so others can
  reproduce it (seeds, environment lockfiles, project structure, data/code availability, Quarto/
  R Markdown). Use it when someone asks for a "Table 1", "how do I report this", "make this
  reproducible", "which reporting guideline applies", "results section", or is preparing a
  manuscript, thesis, or submission.
---

# Reporting and Reproducibility

A result that cannot be reproduced or is reported in a way that misleads is not finished. This
skill makes the writeup honest (effect sizes and uncertainty, not p-value theater), complete (the
guideline checklist for the design), and reproducible (someone else can rerun it and get the same
numbers).

> Run `method-evaluation` first — do not write up an analysis rated `not_ready`. This skill reports
> what the analysis found; it does not rescue a flawed analysis.

## Core workflow

1. **Select the reporting guideline** for the design (it is the checklist your reviewers use):
   CONSORT (RCT), STROBE (cohort/case-control/cross-sectional), TRIPOD (prediction models), PRISMA
   (systematic review/meta-analysis), STARD (diagnostic accuracy), SPIRIT (protocols), CHEERS
   (economic evaluation). See `references/reporting-guidelines.md`.
2. **Draw the participant-flow diagram.** CONSORT flow for trials; a STROBE-style attrition cascade
   for observational studies (N assessed → eligible → analyzed, with reasons/counts at each step).
   This must match the cohort definition from `data-understanding-preprocessing`.
3. **Build Table 1 (baseline characteristics).** Summarize by arm/exposure group with appropriate
   statistics (mean ± SD or median [IQR] for continuous; n (%) for categorical). **In an RCT, do
   not put p-values comparing baseline characteristics across arms** — randomization makes them
   meaningless; report standardized differences if balance is of interest. Use `gtsummary` or
   `tableone` (R) / `tableone` (Python). See `references/reporting-guidelines.md`.
4. **Report the effect properly.** Lead with the **effect size and its confidence interval** on an
   interpretable scale (risk difference, RR, OR, HR, mean difference), then the p-value as context.
   Name the estimand and the model. Report absolute as well as relative effects when possible
   (a relative risk without the baseline risk can mislead).
5. **Make figures that carry the message** — Kaplan–Meier curves with numbers-at-risk, forest
   plots for subgroups/meta-analysis, calibration plots for prediction models, effect plots with
   CIs. Avoid bar-charts-of-means that hide the distribution.
6. **Separate pre-specified from exploratory** results, and state multiplicity handling. Do not
   present a fished subgroup as if it were planned.
7. **Write the limitations honestly** — the biases anticipated at design (`study-design-and-power`)
   and the residual assumptions surfaced by `method-evaluation` (unmeasured confounding,
   missing-data assumptions, generalizability).
8. **Package for reproducibility** (see `references/reproducible-project.md`): a defined project
   structure, a set seed, an environment lockfile (`renv.lock` / `requirements.txt`), recorded
   session info, a literate document (Quarto / R Markdown / Jupyter), and a **data and code
   availability** statement. Aim for: clone → one command → same numbers.

## Reporting discipline

- **Effect size + CI first; p-value second.** Never report "p < 0.05" as the finding.
- **No causal verbs** for associational designs ("associated with", not "reduces"/"causes").
- **Correct effect labels:** odds ratio ≠ risk ratio ≠ hazard ratio; state which and its scale.
- **No baseline p-values in RCT Table 1.**
- **Report what was pre-specified** vs exploratory, and the multiplicity adjustment.
- **Absolute + relative effects** where possible; give the baseline risk.
- **Reproducibility is a deliverable**, not a favor: seed, lockfile, session info, availability
  statement, every time.
- **Meet the reviewer bar.** Before a report is "done," check it against
  `references/reviewer-evidence-checklist.md` — the evidence an editor or reviewer should be able to
  see (estimand, DAG/adjustment set, overlap & balance, missingness method, calibration, validation,
  sensitivity). Turns "we used a tool" into "here is what it required us to show."

## Hand-offs

- Cohort definition & attrition counts → `data-understanding-preprocessing`.
- Effect estimates, model objects, diagnostics → `statistical-analysis`.
- Readiness/critique before writeup → `method-evaluation`.
- Missing-data methods paragraph → `missing-data`.
- Design, estimand, and pre-registration details → `study-design-and-power`.

## Output

Return: (1) the selected reporting guideline and a checklist of what to include; (2) a
participant-flow diagram/spec; (3) Table 1 (correctly constructed for the design); (4) the
effect(s) reported as estimate + CI on a named scale, with absolute and relative where possible;
(5) recommended figures; (6) the pre-specified-vs-exploratory and multiplicity statement; (7) a
limitations paragraph; (8) a reproducibility package (structure, seed, lockfile, session info,
literate document, data/code availability statement).
