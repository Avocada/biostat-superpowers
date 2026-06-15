#!/usr/bin/env bash
#
# Install biostat-superpowers skills for your coding agent.
#
# Usage:
#   ./install.sh            # auto-detect installed agents and link into each
#   ./install.sh codex      # link each skill into ~/.agents/skills (cross-platform; Codex & others)
#   ./install.sh claude     # link each skill into ~/.claude/skills
#   ./install.sh all        # both of the above
#
# This script only creates symlinks pointing back at this repo. Nothing is copied,
# downloaded, or deleted. To uninstall, remove the symlinks it prints.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Link each skill folder individually, so the agent's scanner finds
# <skills_dir>/<skill>/SKILL.md — the layout every skill discovery mechanism understands.
link_each_into() {
  local skills_dir="$1"
  mkdir -p "$skills_dir"
  local d
  for d in "$REPO_DIR"/skills/*/; do
    ln -sfn "${d%/}" "$skills_dir/$(basename "$d")"
    echo "  linked  $skills_dir/$(basename "$d")"
  done
}

install_codex() {
  echo "Codex (~/.codex/skills) + cross-platform agents (~/.agents/skills):"
  [ -d "$HOME/.codex" ] && link_each_into "$HOME/.codex/skills"
  link_each_into "$HOME/.agents/skills"
}

install_claude() {
  echo "Claude Code personal skills (~/.claude/skills):"
  link_each_into "$HOME/.claude/skills"
  echo "  (Cleaner alternative: install as a plugin — see .claude/INSTALL.md)"
}

target="${1:-auto}"
echo "Installing biostat-superpowers from: $REPO_DIR"
echo

case "$target" in
  codex|agents) install_codex ;;
  claude)       install_claude ;;
  all)          install_codex; echo; install_claude ;;
  auto)
    did=0
    if [ -d "$HOME/.codex" ] || [ -d "$HOME/.agents" ]; then install_codex; did=1; fi
    if [ -d "$HOME/.claude" ]; then echo; install_claude; did=1; fi
    if [ "$did" -eq 0 ]; then
      echo "No ~/.codex, ~/.agents, or ~/.claude found. Linking into ~/.agents/skills anyway:"
      install_codex
    fi
    ;;
  *) echo "Unknown target '$target' (use: codex | claude | all | auto)"; exit 1 ;;
esac

echo
echo "Done. Restart your agent, then start by invoking the 'biostatistics' skill"
echo "(or just describe a biomedical research task)."
