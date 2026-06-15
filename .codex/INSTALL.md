# Install biostat-superpowers (Codex & cross-platform agents)

This file is written to be followed by **either a person or a coding agent**. The commands are
the same either way. If you are an agent that a user pointed here, confirm with the user before
running anything that writes to their home directory — this clones a public repo and creates
symlinks.

> One-line way for a user to trigger this: paste into your agent —
> *“Fetch https://raw.githubusercontent.com/z-x-yang/biostat-superpowers/main/.codex/INSTALL.md and follow the instructions.”*

## Steps

1. **Clone (or update) the repository** into a stable location:

   ```bash
   REPO_DIR="$HOME/.codex/biostat-superpowers"
   if [ -d "$REPO_DIR/.git" ]; then
     git -C "$REPO_DIR" pull --ff-only
   else
     git clone --depth 1 \
       https://github.com/z-x-yang/biostat-superpowers "$REPO_DIR"
   fi
   ```

2. **Expose each skill** to Codex's skill directory (`~/.codex/skills`). Link the skill folders
   *individually* so Codex finds `~/.codex/skills/<skill>/SKILL.md` (the layout it scans at
   startup — this is where Codex's other skills live):

   ```bash
   mkdir -p "$HOME/.codex/skills"
   for d in "$REPO_DIR"/skills/*/; do
     ln -sfn "${d%/}" "$HOME/.codex/skills/$(basename "$d")"
   done
   # also expose to the shared cross-platform dir other agents use:
   mkdir -p "$HOME/.agents/skills"
   for d in "$REPO_DIR"/skills/*/; do
     ln -sfn "${d%/}" "$HOME/.agents/skills/$(basename "$d")"
   done
   ```

   (Equivalently, from inside the repo: `./install.sh codex`.)

3. **Restart Codex** so it re-scans for skills.

4. **Verify.** All nine skills should now be discoverable:

   ```bash
   ls "$HOME/.codex/skills"
   # biostatistics  study-design-and-power  data-understanding-preprocessing
   # statistical-analysis  causal-inference  predictive-modeling  missing-data
   # method-evaluation  reporting-and-reproducibility
   ```

## Use it

Start by invoking the **`biostatistics`** skill, or just describe a research task
(“I have an observational cohort and want to estimate a treatment effect — where do I start?”).
The orchestrator routes you to the right specialist. You can also pursue a goal with `/goal`
(e.g. iterative model optimization — see `examples/goal-driven-optimization.md`).

## Uninstall

```bash
for d in "$HOME/.codex/biostat-superpowers"/skills/*/; do
  n="$(basename "$d")"
  rm -f "$HOME/.codex/skills/$n" "$HOME/.agents/skills/$n"   # remove the skill symlinks
done
rm -rf "$HOME/.codex/biostat-superpowers"                    # remove the clone (optional)
```

## Notes

- The skills are linked individually (not as one folder), the layout Codex's skill scanner reads.
- Nothing here installs R or Python packages. The skills generate code and tell you what to run.
