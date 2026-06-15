# Biostatistics Superpowers — agent bootstrap (Codex & other agents)

This repository provides a suite of biomedical-statistics research skills as plain `SKILL.md`
files under [`skills/`](./skills/). They follow the open Agent Skills standard and run on any
agent that can discover and read `SKILL.md` — including OpenAI Codex.

## Use the skills

**Before starting any biomedical-statistics task, check whether a skill applies. If one does,
use it.** Start from the `biostatistics` orchestrator skill; it routes to the right specialist:

- `biostatistics` — orchestrator; routes the whole research lifecycle. **Start here.**
- `study-design-and-power` — question framing, estimand, design choice, sample size & power.
- `data-understanding-preprocessing` — dataset profiling, variable roles, leakage, splits.
- `statistical-analysis` — fitting & interpreting models in R or Python.
- `causal-inference` — effects from observational data (DAGs, PS/IPTW, DiD/IV/RD, E-value).
- `predictive-modeling` — prediction/prognostic models (TRIPOD) & score optimization; leakage-safe CV, calibration, validation.
- `missing-data` — MCAR/MAR/MNAR, multiple imputation, sensitivity analysis.
- `method-evaluation` — adversarial critique of a method; readiness rating + report.
- `reporting-and-reproducibility` — Table 1, effect sizes + CIs, guideline-aligned reporting.

To read a skill, open its `SKILL.md` (e.g. `skills/causal-inference/SKILL.md`) and follow it,
loading the `references/`, `templates/`, and `scripts/` it points to only when needed.

## Tool-name mapping (Claude ↔ Codex)

The skills are written in tool-agnostic language ("read the reference file", "run the script").
Where a skill mentions a Claude Code tool by name, map it to your platform's equivalent:

| Claude Code | Codex equivalent |
|-------------|------------------|
| `Skill` (invoke a skill) | invoke the corresponding `skill` / open its `SKILL.md` |
| `Task` (subagent) | `task` subagent, or run the steps yourself if subagents are unavailable |
| `Read` | `view` |
| `Write` | `create` |
| `Edit` | `edit` |
| `Bash` | `bash` |
| `TodoWrite` | `update_plan` |

If your agent has no subagent mechanism, every skill still works as a linear workflow — none of
them *require* parallel subagents.

## Discipline

These skills encode statistical discipline, not just code. When a skill tells you to specify the
estimand before modeling, check leakage before splitting, or define a baseline before a complex
model — do it, and surface the reasoning to the user.
