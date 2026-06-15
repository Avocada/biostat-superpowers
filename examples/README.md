# Examples

How the skills compose on real biomedical tasks — start with the flagship.

- **[`demo/`](./demo/) — flagship (run by a real agent).** With the suite installed, a coding agent
  given a *one-line plain-English prompt* and a cohort with a **hidden, injected ground truth**
  autonomously ran the whole pipeline (design → leakage audit → confounding adjustment → missing
  data → modeling → self-critique → figures) and **recovered the truth**: it flipped a naively
  "harmful" drug to its true protective effect (RR 0.89, the injected truth was OR 0.70) and
  reported an honest AUC ≈ 0.72 instead of a leakage-inflated 0.98. Includes the agent's verbatim
  analysis, its figures, and a one-command reproduction. A real-data companion
  ([`demo/rhc_causal.py`](./demo/rhc_causal.py)) runs the same causal workflow on the famous
  Right-Heart-Catheterization study (Connors et al., 1996).
- [`observational-cohort-study.md`](./observational-cohort-study.md) — narrative walkthrough: a
  comparative-effectiveness question (drug A vs B on 1-year mortality) from question to manuscript,
  through every skill, showing where each easy-but-fatal mistake gets caught.
- [`goal-driven-optimization.md`](./goal-driven-optimization.md) — narrative walkthrough: using
  `/goal` to iteratively optimize a prediction model **without** overfitting the validation set.
- [`validation/`](./validation/) — synthetic datasets with known ground truth for checking the
  suite recovers the right answer (confounding and leakage traps).

More examples welcome — see [`../CONTRIBUTING.md`](../CONTRIBUTING.md).
