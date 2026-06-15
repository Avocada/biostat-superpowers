# Biostatistics Superpowers — Claude entry point

This repository is a **Claude Code plugin** providing a hierarchy of biomedical-statistics
research skills. The skills live in [`skills/`](./skills/) and are discovered automatically
when the plugin is installed.

## How to use this suite

**Start with the `biostatistics` skill.** It is the orchestrator: it reads the user's
research situation and routes to the right specialist skill (or sequence of skills) for the
job. You do not need to memorize the sub-skills — invoke `biostatistics` and follow its
routing.

If the task is obviously scoped to one phase (e.g. "critique this model"), you may invoke the
relevant specialist skill directly:

| Skill | Use when the task is about… |
|-------|------------------------------|
| `biostatistics` | Anything biomedical-statistical, or you're not sure which sub-skill applies |
| `study-design-and-power` | Framing the question/estimand, choosing a design, sample size & power |
| `data-understanding-preprocessing` | Profiling, validating, and preparing a dataset before modeling |
| `statistical-analysis` | Fitting and interpreting a model in R or Python |
| `causal-inference` | Estimating an effect from observational data |
| `predictive-modeling` | Building/validating a prediction model, or optimizing a predictive score |
| `missing-data` | Diagnosing missingness and doing multiple imputation / sensitivity analysis |
| `method-evaluation` | Critiquing whether a method/analysis is appropriate and trustworthy |
| `reporting-and-reproducibility` | Producing Table 1, effect sizes + CIs, guideline-aligned reporting, reproducible code |

## Operating principle

These skills encode statistical *discipline*, not just code. When a skill says to specify the
estimand before modeling, check leakage before splitting, or define the baseline before the
complex model — follow it. The value of the suite is that it stops plausible-but-wrong analyses
before they happen.
