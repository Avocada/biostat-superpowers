# Install this fork in Claude Code

The current fork is **Avocada/biostat-superpowers**; its default branch is **v2**.

## Skills through the plugin

In Claude Code:

```text
/plugin marketplace add Avocada/biostat-superpowers
/plugin install biostat-superpowers@biostat-superpowers
```

The fork and upstream use the same marketplace name. If you already installed the upstream marketplace, inspect it first. To intentionally switch, remove the old marketplace registration and add the fork, then reinstall the plugin. Removing a marketplace can affect other plugins installed from it; preserve an existing setup unless the switch is intended. Do not install the same skills through both plugin and manual links.

The plugin exposes the nine original statistical skills plus `biostat-workflow`. **It does not install the Python environment or automatically register the MCP server.** Complete the [runtime and MCP setup](../docs/modernization/INSTALL_V2.md), including the Claude-specific registration command. When reading raw files, fetch https://raw.githubusercontent.com/Avocada/biostat-superpowers/v2/docs/modernization/INSTALL_V2.md.

## Manual alternative

Use the separate v2 runtime checkout from that guide and run:

```sh
bash "$BIOSTAT_DIR/install.sh" claude
```

This creates ten links under `~/.claude/skills`. For an existing original skill installation, follow the guide's companion-only instructions with `BIOSTAT_SKILLS_DIR="$HOME/.claude/skills"`. Inspect existing destinations before replacing anything.

## Verify and update

Start a fresh session and ask which biostatistics skills are available; use `claude mcp list` to check the separately registered server. For runtime updates, follow the v2 guide. For plugin updates, refresh the configured fork marketplace and update the installed plugin through Claude's plugin manager. Keep the companion and runtime aligned.

To uninstall, use `/plugin uninstall biostat-superpowers` for the plugin, or remove only the manual symlinks pointing to this checkout. Use `claude mcp remove biostat` to remove the server registration. Preserve research artifacts and project memory.

Reference: [Claude marketplace documentation](https://code.claude.com/docs/en/plugin-marketplaces).
