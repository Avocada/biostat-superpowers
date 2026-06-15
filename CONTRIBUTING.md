# Contributing to Biostatistics Superpowers

Thanks for helping make rigorous biomedical statistics accessible to research agents. Skills,
references, additional languages, worked examples, and fixes are all welcome.

## Ground rules

1. **Tool-agnostic `SKILL.md`.** Write skills so they run on *any* agent. Say "read the
   reference file" / "run the script", not "use the Read tool". This is what makes the suite
   work on both Claude Code and Codex. (See `AGENTS.md` for the tool mapping.)
2. **Statistical claims must be defensible and sourced.** Tie guidance to established practice
   (Harrell; Hernán & Robins; van Buuren; Gelman/Hill/Vehtari; Hastie/Tibshirani/Friedman;
   reporting guidelines). Do not invent thresholds or "rules of thumb" without provenance.
3. **R and Python parity.** New analysis content should provide both an R and a Python path, or
   clearly state why one is omitted.
4. **No silent data destruction.** Any code that drops rows/columns must record the rule, the
   count affected, and the rationale.
5. **Honesty over confidence.** Skills should surface assumptions and route hard calls back to
   the user — never paper over an identifiability or validity problem.

## Anatomy of a skill

```
skills/<skill-name>/
├── SKILL.md            # required: frontmatter (name, description) + the workflow
├── references/         # optional: deep-dive docs loaded on demand (progressive disclosure)
├── templates/          # optional: method-family checklists, report skeletons
└── scripts/            # optional: runnable R/Python helpers
```

### `SKILL.md` frontmatter

```yaml
---
name: skill-name                 # kebab-case, matches the folder
description: >
  One or two sentences in the third person describing WHEN to use this skill and WHAT it
  produces. This is the only text the agent sees during routing, so make the trigger concrete.
---
```

Keep `SKILL.md` itself lean (a workflow + a map of what to read when). Push detail into
`references/` so the agent loads it only when relevant — this is *progressive disclosure* and it
keeps the skill cheap to route to.

## Adding a skill

1. Create `skills/<skill-name>/SKILL.md` following the conventions above.
2. Register it in the orchestrator (`skills/biostatistics/SKILL.md`) routing table, in this
   `CONTRIBUTING.md` is not needed, but update `README.md`, `CLAUDE.md`, and `AGENTS.md` skill
   lists.
3. Cross-link related skills by name so the agent can hand off.
4. If you add runnable code, make it check for missing packages and never overwrite raw input.

## Testing a skill

Skills are prompts, so "tests" are scenario checks:

- Does routing reach the skill from a realistic user request?
- Does the workflow produce the stated output sections?
- Does generated R/Python run on a small synthetic dataset?
- Does the skill correctly *refuse* or *route away* when the task is out of scope?

## Pull requests

Keep PRs focused (one skill or one coherent improvement). Describe the statistical rationale,
not just the diff. By contributing you agree to license your work under the repository's
[MIT License](./LICENSE).
