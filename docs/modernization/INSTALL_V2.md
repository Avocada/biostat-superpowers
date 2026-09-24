# Install the optional v2 runtime and companion skill

The original nine domain skills remain unchanged. The additional `biostat-workflow` skill explains how to use executable state gates, project memory and MCP tools. Installing Python code alone does not make those components run automatically.

Use a separate stable checkout so updates do not repoint the original skill installation:

```sh
git clone --branch v2 https://github.com/Avocada/biostat-superpowers.git ~/.codex/biostat-superpowers-v2
python3 -m venv ~/.codex/biostat-superpowers-v2/.venv
~/.codex/biostat-superpowers-v2/.venv/bin/python -m pip install -e "$HOME/.codex/biostat-superpowers-v2[mcp]"
```

Install `skills/biostat-workflow` from the same GitHub branch using the host's skill installer, or link only that additional directory into its skill directory. Pin the same commit for the runtime and companion skill. Existing domain skills can continue to use their original checkout because their policies have not changed.

For Codex, register the stable server path (choose an artifact directory for your project):

```sh
codex mcp add biostat -- "$HOME/.codex/biostat-superpowers-v2/.venv/bin/biostat-mcp" --artifact-dir "$HOME/.codex/biostat-superpowers-v2/outputs/mcp"
```

The companion skill will be available on the next turn. A fresh server process uses the new MCP registration. Invoke `biostat-workflow` alongside `biostatistics` for an instrumented study. Ordinary skill-only usage remains supported. Jev is deferred and no routing-model API key is needed.

Validate from the runtime checkout with `.venv/bin/python -B -m unittest discover -s tests -q`. The causal demonstration and source handoff demonstration are documented separately; automated checks do not certify statistical validity. Analysis-specific dependencies belong in a separate analysis environment.
