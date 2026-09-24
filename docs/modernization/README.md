# Modernization groundwork

Prepared 2026-09-23. This branch establishes the development baseline and now includes the first executable workflow-controller increment. An optional project-memory layer and paired context-token demo are also implemented; an optional local MCP server is now implemented. Jev (TypeSafe AI) routing is optional and deferred; the next priority is end-to-end behavioral evaluation.

See [WORKFLOW_CONTROLLER.md](WORKFLOW_CONTROLLER.md) for the architecture, state/result contract, stop policies, demo commands, validation, and remaining work. The optional standard-library Python runtime is in `biostat_workflow/`; existing declarative and installed skills are unchanged.

See [MEMORY.md](MEMORY.md) for confirmed project memory, context selection, invalidation, the measured token comparison, and its limitations.

See [MCP_SERVER.md](MCP_SERVER.md) for the optional stdio server, UCI retrieval, local profiling/visualization, resource catalog, setup and protocol demo. See [CLINICAL_TRIALS.md](CLINICAL_TRIALS.md) for live trial search, details, pagination and comparison charts. [LITERATURE.md](LITERATURE.md) covers PubMed/Europe PMC citation retrieval and provenance-preserving reference lists. [REVIEWED_HANDOFF.md](REVIEWED_HANDOFF.md) connects source-reviewed proposals to confirmed project memory and versioned workflow checkpoints.

## Repository setup

- Personal fork: https://github.com/Avocada/biostat-superpowers
- Original upstream: https://github.com/z-x-yang/biostat-superpowers
- Local development checkout: `/Users/amiee/Projects_code/biostat-superpowers`
- Development branch: `v2`
- Baseline commit: `a1007c3e0a295a294fab21bd7ee94565c55f9916`
- `origin` targets the personal fork; `upstream` targets the original project.
- Installed skills still use `/Users/amiee/.codex/biostat-superpowers`. Do not run the installer from this development checkout until deliberately testing an installation.

The upstream clone is a complete Git repository used as the backing store for installed skill symlinks. Keeping a separate development checkout prevents work in progress from changing the installed skills.

## Baseline inventory

| Area | Evidence in the baseline | Work to consider |
|---|---|---|
| Specialist routing | Nine skill directories: one orchestrator and eight specialists; `skills/biostatistics/SKILL.md` | Machine-readable route and handoff records |
| Workflow graph and revision loop | Described in the orchestrator and README | Executable transitions, bounded retries, checkpoint/resume |
| Method evaluation | Reviewer skill, rubric, templates, JSON report schema | Automated regression evaluation of agent behavior |
| Validation | Routing scenarios, transcripts, synthetic data and worked demos | Repeatable evaluation runner and comparable run reports |
| Persistent project memory | No dedicated memory implementation identified | Explicit scope, provenance, corrections and invalidation |
| MCP integration | No dedicated MCP server/client configuration or adapter identified | Optional adapters with typed inputs, results and failure handling |
| Fast/slow decision routing | No dedicated runtime policy identified | Measurable escalation policy with a careful default |
| Build automation | No tracked `.github/` workflows or top-level `tests/` found | Lightweight structural checks, followed by behavioral evaluation |

The baseline graph, loop and evaluation were primarily instructions and examples. The new controller executes prerequisite routing and bounded revision loops with synthetic handoffs. It does not yet execute statistical specialists or evaluate model behavior.

## Proposed scope

The planned MCP milestone is considered complete. Jev refers to TypeSafe AI’s structured decision model. Its integration is deferred by user decision: the existing deterministic lifecycle router needs no model calls, and an additional intent-routing service has not demonstrated a net benefit. See the routing decision in [ROADMAP.md](ROADMAP.md). No Jev dependency or API integration is enabled; Laya is outside the current scope.

See [ROADMAP.md](ROADMAP.md) for staged work and acceptance criteria. Keep the original methodology skills usable independently of any new runtime. Preserve upstream attribution and MIT licensing.

## Development workflow

Work on focused feature branches from this baseline; push to `origin`. Use `upstream` to inspect and incorporate original-project updates deliberately. Avoid changing installed skill links during development. Use synthetic data in repository examples and evaluation fixtures.

For an initial inspection:

```sh
git remote -v
git status --short --branch
git log -1 --oneline
```

Original groundwork verification checked fork ancestry, branch/remotes, the baseline commit, documentation links and the diff. Controller validation now uses `python3 -B -m unittest discover -s tests -v` and the synthetic demos documented above. No model-quality or clinical-analysis validation is claimed.

## Optional installation and workflow illustrations

See [INSTALL_V2.md](INSTALL_V2.md) for the separate runtime installation and additional `biostat-workflow` skill. The original specialist policies remain unchanged.

The revised [version 1 figure](figures/modern_ai_agent_system_v1.png) and [version 2 figure](figures/modern_ai_agent_system_v2.png) omit Jev, the separate model-routing diamond and the System 2 label. These are conceptual illustrations; the implementation scope and review limitations are defined in the architecture documents above. Deterministic lifecycle routing remains implemented in the controller.

The [RHC paired reproduction](../../examples/rhc_comparison/RESULTS.md) applies the installed runtime to the original real-data example, with explicit limits on causal readiness and efficiency claims.
