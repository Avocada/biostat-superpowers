# Install this fork in Codex

For the current workflow, memory and MCP capabilities, use **Avocada/biostat-superpowers, branch v2**, not the original upstream main branch.

One-line request:

> Fetch https://raw.githubusercontent.com/Avocada/biostat-superpowers/v2/.codex/INSTALL.md and install the skills plus the optional workflow, memory and MCP runtime. Preserve my existing domain-skill installation.

Follow the complete [v2 installation guide](../docs/modernization/INSTALL_V2.md). If reading this through a raw URL, retrieve https://raw.githubusercontent.com/Avocada/biostat-superpowers/v2/docs/modernization/INSTALL_V2.md next.

The guide covers:

1. A separate `~/.codex/biostat-superpowers-v2` checkout and Python 3.10+ environment.
2. Ten skills for a fresh install, or only `biostat-workflow` alongside nine existing domain skills.
3. Installing the `[mcp]` dependency extra and registering `biostat` with `codex mcp add`.
4. Optional staged local CSV access, verification, updates and removal.

For **skills only**, clone the v2 checkout and run `bash "$BIOSTAT_DIR/install.sh" codex` as described in the guide. That creates skill links but does not install Python dependencies or enable MCP. `biostat-workflow` describes runtime use; its executable capabilities remain unavailable until runtime setup is complete.

Use the user's authorized installation scope; inspect existing destinations before replacing anything. Do not silently repoint an original skill checkout or create duplicate skill installations. The current Codex user skill directory is `~/.agents/skills`; the installer also supports legacy `~/.codex/skills` installations. See [official skill discovery](https://learn.chatgpt.com/docs/build-skills).
