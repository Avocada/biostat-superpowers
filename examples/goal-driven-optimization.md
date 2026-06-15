# Worked example: `/goal`-driven model optimization, done rigorously

Both Claude and Codex support `/goal` — set a target and the agent keeps working until it's met.
That is exactly how you want to *optimize a model's performance*: iterate features, models, and
tuning until the metric clears a bar. The danger is that a naive optimize-until-the-number-goes-up
loop **overfits to the validation set** (adaptive overfitting / leaderboard overfitting) — the
score rises while true performance does not. `predictive-modeling` makes the loop honest.

> **The goal.** "Get nested-CV AUROC for 30-day readmission to ≥ 0.80 without leakage."

## Setting it up

```
/goal Use the `predictive-modeling` skill to raise nested-CV AUROC for 30-day readmission to
      ≥ 0.80 without leakage. Keep a final test set untouched until the very end, optimize only
      on cross-validation, and stop if three consecutive rounds give no out-of-fold gain.
```

The skill turns that into a disciplined loop with a real finish line.

## What each iteration does (and what it refuses to do)

1. **Lock the protocol once (round 0).** Define the outcome and prediction time, split off a
   **final test set that is touched exactly once at the end**, and set the resampling scheme
   (nested CV / grouped by patient / time-based if prospective). Route the split + leakage audit
   to `data-understanding-preprocessing`.
2. **Each round, inside the CV folds only:**
   - engineer/clean features with all learned transforms fit *inside* the fold,
   - try a model class or tuning change (regularized regression → gradient boosting → ensemble),
   - measure the target metric out-of-fold, and **also** check calibration,
   - compare against the running best and the baseline.
3. **Log the round:** what changed, out-of-fold AUROC, calibration slope, and whether the gain is
   within noise.
4. **Stop rule:** stop when the goal is met *and* holds, or after the plateau (three flat rounds).

## The guard rail that makes `/goal` safe here

A loop that keeps selecting on the same validation data will eventually "find" gains that are
noise — the metric becomes a liar. `predictive-modeling` enforces:

- **Optimize on (nested) CV, never on the final test set.** The test set is opened once, at the
  end, to report honest performance.
- **Bound the search.** Too many evaluations against one validation set = adaptive overfitting.
  Prefer nested CV; track how many configurations were tried.
- **Confirm generalization, not just the number.** A round only "counts" if the out-of-fold gain
  survives on the untouched test/external set at the end. If CV says 0.83 but the held-out test
  says 0.74, the loop was fitting noise — report the honest number and say so.
- **Calibration is part of the goal**, not just discrimination — a high-AUROC, miscalibrated model
  is not "done" for a clinical decision.

## A plausible run

| Round | Change | OOF AUROC | Calib. slope | Kept? |
|---|---|---|---|---|
| 0 | baseline: logistic regression, core features | 0.71 | 0.98 | baseline |
| 1 | + leakage-safe feature engineering | 0.75 | 0.95 | ✓ |
| 2 | gradient-boosted trees, tuned by nested CV | 0.79 | 0.88 | ✓ (recalibrate) |
| 3 | isotonic recalibration | 0.79 | 0.99 | ✓ |
| 4 | ensemble (LR + GBM, out-of-fold stacking) | 0.81 | 0.97 | ✓ — goal met |
| 5 | more aggressive tuning | 0.815 | 0.96 | ✗ within noise → plateau |

**Finish:** open the untouched test set once → AUROC 0.80, calibration slope 0.98. The goal is met
*and* generalizes. Report the optimism-corrected, held-out number (not the 0.815 CV peak), per
**TRIPOD**, via `reporting-and-reproducibility`.

## Why this matters

Without the guard rails, `/goal "raise AUROC to 0.85"` will happily report 0.85 — by overfitting
the validation set — and the model will disappoint in production or peer review. The same loop,
run through `predictive-modeling`, either reaches a number you can trust or tells you honestly that
the signal isn't there. That is the difference between a score and a result.
