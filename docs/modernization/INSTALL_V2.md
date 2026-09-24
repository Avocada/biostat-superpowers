# Install the v2 skills, workflow, memory and MCP server

Use **Avocada/biostat-superpowers**, branch **v2**. The original nine statistical skills remain the domain-policy layer; `biostat-workflow` is the tenth, optional companion. Installing skills alone does not install or activate the Python runtime. Jev is not implemented.

These are macOS/Linux shell commands. Prerequisites: Git, Python 3.10+ with venv/pip, and your host's CLI. The local server uses stdio; no hosted server or API key is required for the built-in public sources. Downloads require network access. Install analysis-specific R/Python packages in a separate analysis environment.

## Runtime checkout and dependencies

For a new, separate runtime checkout:

```sh
BIOSTAT_DIR="$HOME/.codex/biostat-superpowers-v2"
git clone --branch v2 https://github.com/Avocada/biostat-superpowers.git "$BIOSTAT_DIR"
python3 -m venv "$BIOSTAT_DIR/.venv"
"$BIOSTAT_DIR/.venv/bin/python" -m pip install -e "${BIOSTAT_DIR}[mcp]"
```

The quoted editable-install path is intentional: it preserves spaces and prevents shell expansion of `[mcp]`. This installs the workflow/memory package, pinned MCP SDK and chart renderer; it does not install a language model or analysis libraries. A clone of the runtime is needed even when skills were installed through a plugin.

## Fresh skill installation

Choose the appropriate host:

```sh
bash "$BIOSTAT_DIR/install.sh" codex
# Or, for a manual Claude skill install instead of its plugin:
# bash "$BIOSTAT_DIR/install.sh" claude
```

This links all ten skills. Codex links go to `~/.agents/skills`, plus `~/.codex/skills` for compatibility when that directory's parent exists. Claude manual links go to `~/.claude/skills`. The installer replaces same-name symlinks; use the next section to preserve an existing domain-skill installation. Do not install the same skill set through both a plugin and manual links.

## Existing domain-skill installation

Keep the original checkout and domain-skill links. Add only the companion in one skill directory; use the same directory as the existing skills (current Codex defaults to `~/.agents/skills`, older installations may use `~/.codex/skills`, Claude uses `~/.claude/skills`). For example:

```sh
BIOSTAT_SKILLS_DIR="$HOME/.agents/skills"
mkdir -p "$BIOSTAT_SKILLS_DIR"
if [ -e "$BIOSTAT_SKILLS_DIR/biostat-workflow" ] || [ -L "$BIOSTAT_SKILLS_DIR/biostat-workflow" ]; then
  printf '%s\n' 'Companion already exists; inspect its source rather than replacing it.'
else
  ln -s "$BIOSTAT_DIR/skills/biostat-workflow" "$BIOSTAT_SKILLS_DIR/biostat-workflow"
fi
```

Ensure an existing companion points to the intended v2 runtime. Avoid adding a second copy in a different discovery directory.

## Register MCP

For Codex:

```sh
codex mcp add biostat -- "$BIOSTAT_DIR/.venv/bin/biostat-mcp" --artifact-dir "$BIOSTAT_DIR/outputs/mcp"
codex mcp list
```

For Claude Code, register the same executable at user scope:

```sh
claude mcp add --transport stdio --scope user biostat -- "$BIOSTAT_DIR/.venv/bin/biostat-mcp" --artifact-dir "$BIOSTAT_DIR/outputs/mcp"
claude mcp list
```

If `biostat` already exists, inspect its command first; do not create duplicate registrations. If its executable or arguments need changing, remove that named registration and add it again. Stable paths do not require re-registration after every code update.

Local CSV import is disabled unless you explicitly configure a staging directory. To enable it, add `--input-dir "/absolute/path/to/staged-csv"` after the server's artifact argument, then re-register/restart. Use an existing, deliberate staging folder. Artifacts and project decisions are saved locally; do not commit patient data or memory databases. The MCP server does not independently approve a handoff or upload participant matrices to the public evidence sources.

## Verify and use

```sh
"$BIOSTAT_DIR/.venv/bin/biostat-mcp" --help
"$BIOSTAT_DIR/.venv/bin/python" -B -m unittest discover -s "$BIOSTAT_DIR/tests" -q
```

The suite currently has 140 tests. In a fresh host session, confirm the server exposes 22 tools, including `annotate_proteins`, `get_target_evidence`, `search_trials`, `search_literature`, `render_chart` and `get_project_context`. Automated tests validate software behavior, not scientific correctness or continued availability of live APIs.

Example request:

> Use biostatistics and biostat-workflow to define my analysis question, verify the data, record project decisions and retrieve relevant external evidence through MCP. Save source provenance and identify unresolved scientific assumptions.

Skills are detected by the host; restart if changes are not picked up. A fresh MCP process is needed after runtime updates. Memory persists only when the workflow actually records and retrieves decisions; it is not automatic conversation replay or a guarantee of token savings.

## Update

With a clean v2 checkout and the intended origin:

```sh
BIOSTAT_DIR="$HOME/.codex/biostat-superpowers-v2"
git -C "$BIOSTAT_DIR" remote get-url origin
git -C "$BIOSTAT_DIR" status --short
git -C "$BIOSTAT_DIR" switch v2
git -C "$BIOSTAT_DIR" pull --ff-only origin v2
"$BIOSTAT_DIR/.venv/bin/python" -m pip install -e "${BIOSTAT_DIR}[mcp]"
```

Preserve local edits; do not reset an unrelated upstream checkout. Keep the runtime and companion on the same revision. Existing original domain skills may remain on their original revision. Restart the agent/server and rerun verification.

## Remove

Use `codex mcp remove biostat` or `claude mcp remove biostat` for the relevant host. Remove only symlinks you confirmed point to this checkout. Keep analysis artifacts and project memory until you deliberately choose to delete them; uninstalling should not silently remove research records.

References: [Codex skill discovery](https://learn.chatgpt.com/docs/build-skills), [Codex MCP configuration](https://learn.chatgpt.com/docs/extend/mcp?surface=cli), [Claude MCP setup](https://code.claude.com/docs/en/mcp). Tool scope: [MCP_SERVER.md](MCP_SERVER.md), [OMICS_MCP.md](OMICS_MCP.md).
