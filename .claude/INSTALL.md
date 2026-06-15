# Install Biostatistics Superpowers (Claude Code)

This file is written to be followed by **either a person or a coding agent**. The commands are
the same either way. If you are an agent a user pointed here, confirm before running anything
that writes to their home directory.

There are two ways to install. **The plugin route is recommended** (cleaner updates, proper
namespacing); the manual route is a fallback that an agent can run end-to-end.

## Option A — Install as a plugin (recommended)

Run these in Claude Code (replace `z-x-yang`):

```text
/plugin marketplace add z-x-yang/biostat-superpowers
/plugin install biostat-superpowers@biostat-superpowers
```

Or open the interactive menu with `/plugin` and install it from the marketplace. These are slash
commands a **person** runs in the Claude Code prompt (an agent cannot type slash commands for
you — if you're an agent, use Option B).

## Option B — Manual install into personal skills

1. **Clone (or update)** the repository:

   ```bash
   REPO_DIR="$HOME/.claude/biostat-superpowers"
   if [ -d "$REPO_DIR/.git" ]; then
     git -C "$REPO_DIR" pull --ff-only
   else
     git clone --depth 1 \
       https://github.com/z-x-yang/biostat-superpowers "$REPO_DIR"
   fi
   ```

2. **Link each skill** into your personal skills directory (Claude Code's personal-skill
   discovery looks for `~/.claude/skills/<skill>/SKILL.md`):

   ```bash
   mkdir -p "$HOME/.claude/skills"
   for d in "$REPO_DIR"/skills/*/; do
     ln -sfn "${d%/}" "$HOME/.claude/skills/$(basename "$d")"
   done
   ```

   (Equivalently, from inside the repo: `./install.sh claude`.)

3. **Restart Claude Code** (or run `/doctor`) so it re-scans skills.

## Verify

Ask Claude: *“What skills do you have available?”* — you should see `biostatistics` and its eight
specialist skills. Then start with the **`biostatistics`** skill or just describe a research task.

## Uninstall

- Plugin: `/plugin uninstall biostat-superpowers`
- Manual: remove the symlinks from `~/.claude/skills/` and delete the clone.
