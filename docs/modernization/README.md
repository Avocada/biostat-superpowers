# Modernization groundwork

Prepared 2026-09-23. This branch establishes a development baseline and a proposed implementation plan. It does not implement the proposed components.

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

The existing graph, loop and evaluation are primarily instructions and examples. A future runtime must demonstrate execution behavior before those capabilities are advertised as implemented.

## Proposed scope

Starting candidates come from the earlier before/after diagram: memory, MCP connections and fast/slow decision routing. These are planning assumptions, not a finalized requirement list. The specific meaning of “Jev / Laya” from the earlier conversation remains unresolved; no dependency or model is selected on that basis.

See [ROADMAP.md](ROADMAP.md) for staged work and acceptance criteria. Keep the original methodology skills usable independently of any new runtime. Preserve upstream attribution and MIT licensing.

## Development workflow

Work on focused feature branches from this baseline; push to `origin`. Use `upstream` to inspect and incorporate original-project updates deliberately. Avoid changing installed skill links during development. Use synthetic data in repository examples and evaluation fixtures.

For an initial inspection:

```sh
git remote -v
git status --short --branch
git log -1 --oneline
```

Groundwork verification consists of checking fork ancestry, branch/remotes, the baseline commit, documentation links and the final diff. No model or analysis tests are claimed for this documentation-only change.
