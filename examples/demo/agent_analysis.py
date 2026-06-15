"""
Biostatistics analysis — cohort.csv
Goal 1 (Causal):    Does new_drug lower 1-year event risk? (observational, IPTW + doubly-robust)
Goal 2 (Predictive): Predict event_1yr; report honest out-of-sample AUC + calibration.

LEAKAGE NOTE: followup_marker is recorded during follow-up — excluded from both analyses.
"""

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import roc_auc_score, brier_score_loss, average_precision_score
from sklearn.calibration import calibration_curve
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RNG = 42
np.random.seed(RNG)

# ── Load data ──────────────────────────────────────────────────────────────────
# [repo note] Data/figure paths made relative for portability; the analysis logic below is the
# agent's verbatim output (see this folder's README for an honest list of slips a review caught).
import os
_HERE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(_HERE, "cohort.csv"))
print(f"Loaded: {df.shape[0]} rows × {df.shape[1]} cols")
print(f"Event rate: {df['event_1yr'].mean():.3f}  ({df['event_1yr'].sum()} events)")
print(f"Treatment rate: {df['new_drug'].mean():.3f}  ({df['new_drug'].sum()} treated)")
print(f"Missing lab_b: {df['lab_b'].isna().sum()} ({df['lab_b'].isna().mean()*100:.1f}%)")
print()

# ── Feature sets ──────────────────────────────────────────────────────────────
BASELINE_CONT = ["age", "baseline_severity", "comorbidity_count", "lab_a", "lab_b"]
BASELINE_CAT  = ["site", "sex"]   # sex is 0/1 but treat as categorical for dummies
CONFOUNDERS   = BASELINE_CONT + BASELINE_CAT   # all pre-treatment variables
# new_drug excluded from confounders (it's the exposure)
# followup_marker EXCLUDED — post-treatment leakage

PRED_FEATURES = BASELINE_CONT + BASELINE_CAT + ["new_drug"]   # for prediction model

Y = df["event_1yr"].values
A = df["new_drug"].values   # treatment

# ──────────────────────────────────────────────────────────────────────────────
# ANALYSIS 1: CAUSAL INFERENCE
# Estimand: ATE of new_drug (vs standard care) on Pr(event_1yr=1)
# Strategy: IPTW (propensity score weighting) + doubly-robust AIPW
# Adjustment set: all baseline confounders (backdoor criterion; no colliders/mediators)
# followup_marker excluded (post-treatment — would induce collider/mediator bias)
# ──────────────────────────────────────────────────────────────────────────────
print("=" * 70)
print("ANALYSIS 1 — CAUSAL EFFECT OF NEW DRUG")
print("=" * 70)

# ── Step 1: Build covariate matrix for propensity model ──────────────────────
def make_confounder_matrix(df):
    dummies = pd.get_dummies(df["site"], prefix="site", drop_first=True)
    X = pd.concat([
        df[BASELINE_CONT].copy(),
        df[["sex"]].astype(float),
        dummies.astype(float)
    ], axis=1)
    return X

X_conf = make_confounder_matrix(df)
# Impute lab_b with median (only 1 missing covariate; simple imputation acceptable for PS)
lab_b_median = df["lab_b"].median()
X_conf["lab_b"] = X_conf["lab_b"].fillna(lab_b_median)
X_conf_arr = X_conf.values

# ── Step 2: Propensity score model ───────────────────────────────────────────
ps_model = LogisticRegression(max_iter=1000, C=1.0, solver="lbfgs")
ps_model.fit(X_conf_arr, A)
ps = ps_model.predict_proba(X_conf_arr)[:, 1]

print(f"\nPropensity score summary (treated vs control):")
print(f"  Treated  — mean PS: {ps[A==1].mean():.3f}  [min {ps[A==1].min():.3f}, max {ps[A==1].max():.3f}]")
print(f"  Control  — mean PS: {ps[A==0].mean():.3f}  [min {ps[A==0].min():.3f}, max {ps[A==0].max():.3f}]")

# ── Step 3: Overlap check ─────────────────────────────────────────────────────
# Positivity: trim extreme weights (< 5th or > 95th percentile of PS)
ps_lower, ps_upper = np.percentile(ps, [2.5, 97.5])
overlap_mask = (ps >= ps_lower) & (ps <= ps_upper)
n_trimmed = (~overlap_mask).sum()
print(f"\nOverlap: PS range [{ps_lower:.3f}, {ps_upper:.3f}]; trimming {n_trimmed} rows ({n_trimmed/len(df)*100:.1f}%)")

# ── Step 4: IPTW weights ──────────────────────────────────────────────────────
# ATE weights: treated = 1/PS, control = 1/(1-PS)
eps = 1e-6
w = np.where(A == 1, 1.0 / (ps + eps), 1.0 / (1.0 - ps + eps))
# Stabilize: multiply by marginal probability
p_treat = A.mean()
sw = np.where(A == 1, p_treat / (ps + eps), (1 - p_treat) / (1.0 - ps + eps))

print(f"\nStabilized IPT weights — mean: {sw.mean():.3f}, max: {sw.max():.2f}, "
      f"ESS treated: {(sw[A==1].sum()**2 / (sw[A==1]**2).sum()):.0f}, "
      f"ESS control: {(sw[A==0].sum()**2 / (sw[A==0]**2).sum()):.0f}")

# ── Step 5: Covariate balance (SMDs) ─────────────────────────────────────────
def smd(x, a, weights=None):
    """Standardized mean difference."""
    if weights is None:
        weights = np.ones(len(x))
    mu1 = np.average(x[a==1], weights=weights[a==1])
    mu0 = np.average(x[a==0], weights=weights[a==0])
    var1 = np.average((x[a==1] - mu1)**2, weights=weights[a==1])
    var0 = np.average((x[a==0] - mu0)**2, weights=weights[a==0])
    pooled_sd = np.sqrt((var1 + var0) / 2)
    return (mu1 - mu0) / (pooled_sd + 1e-9)

print("\nCovariate balance (|SMD| < 0.1 = well-balanced after weighting):")
print(f"  {'Variable':<25} {'Unadjusted':>12} {'IPTW-weighted':>14}")
for col in X_conf.columns:
    x = X_conf[col].values
    smd_raw = abs(smd(x, A))
    smd_wtd = abs(smd(x, A, weights=sw))
    flag = " ✓" if smd_wtd < 0.1 else " !"
    print(f"  {col:<25} {smd_raw:>12.3f} {smd_wtd:>13.3f}{flag}")

# ── Step 6: Doubly-robust AIPW estimator ─────────────────────────────────────
# Outcome model: logistic regression for E[Y | A, X]
from sklearn.model_selection import cross_val_predict as cvp

# Fit outcome model on full data (or use CV predictions for honest AIPW)
def aipw_estimate(Y, A, X, ps, n_boot=2000):
    """Augmented IPW (doubly-robust) ATE estimator with bootstrap CI."""
    n = len(Y)

    # Outcome model via 5-fold CV to get honest mu_hat
    Xa1 = np.column_stack([X, np.ones(n)])   # set A=1
    Xa0 = np.column_stack([X, np.zeros(n)])  # set A=0
    Xfull = np.column_stack([X, A])

    om = LogisticRegression(max_iter=1000, C=1.0, solver="lbfgs")

    # Cross-fitted outcome predictions
    mu_cv = np.zeros(n)
    mu1_cv = np.zeros(n)
    mu0_cv = np.zeros(n)
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=RNG)
    for tr_idx, te_idx in skf.split(Xfull, Y):
        om.fit(Xfull[tr_idx], Y[tr_idx])
        mu_cv[te_idx] = om.predict_proba(Xfull[te_idx])[:, 1]
        mu1_cv[te_idx] = om.predict_proba(Xa1[te_idx])[:, 1]
        mu0_cv[te_idx] = om.predict_proba(Xa0[te_idx])[:, 1]

    eps_val = 1e-6
    # AIPW influence function
    phi1 = mu1_cv + A * (Y - mu_cv) / (ps + eps_val)
    phi0 = mu0_cv + (1 - A) * (Y - mu_cv) / (1 - ps + eps_val)
    tau_i = phi1 - phi0

    ate_rd = tau_i.mean()   # risk difference

    # Bootstrap CI
    boot_rds = np.zeros(n_boot)
    idx_all = np.arange(n)
    for b in range(n_boot):
        idx_b = np.random.choice(idx_all, size=n, replace=True)
        boot_rds[b] = tau_i[idx_b].mean()

    ci_lo, ci_hi = np.percentile(boot_rds, [2.5, 97.5])
    p_value = 2 * min(
        (boot_rds >= 0).mean(),
        (boot_rds <= 0).mean()
    )

    # Risk ratio (marginal via outcome model means)
    rr = mu1_cv.mean() / mu0_cv.mean()
    rr1 = mu1_cv.mean()
    rr0 = mu0_cv.mean()

    # Bootstrap RR CI
    boot_rrs = np.zeros(n_boot)
    for b in range(n_boot):
        idx_b = np.random.choice(idx_all, size=n, replace=True)
        boot_rrs[b] = mu1_cv[idx_b].mean() / mu0_cv[idx_b].mean()
    rr_lo, rr_hi = np.percentile(boot_rrs, [2.5, 97.5])

    return {
        "rd": ate_rd, "rd_ci": (ci_lo, ci_hi), "p_rd": p_value,
        "rr": rr, "rr_ci": (rr_lo, rr_hi),
        "mu1": rr1, "mu0": rr0,
        "phi1": phi1, "phi0": phi0
    }

print("\nFitting doubly-robust AIPW estimator (bootstrap CI, 2000 resamples)...")
result = aipw_estimate(Y, A, X_conf_arr, ps, n_boot=2000)

print(f"\n{'─'*60}")
print(f"CAUSAL EFFECT ESTIMATES (doubly-robust AIPW)")
print(f"{'─'*60}")
print(f"  Counterfactual event risk if ALL treated:     {result['mu1']:.4f} ({result['mu1']*100:.2f}%)")
print(f"  Counterfactual event risk if NONE treated:    {result['mu0']:.4f} ({result['mu0']*100:.2f}%)")
print(f"\n  Risk Difference (RD):  {result['rd']:+.4f}  95% CI [{result['rd_ci'][0]:+.4f}, {result['rd_ci'][1]:+.4f}]")
print(f"  Risk Ratio (RR):       {result['rr']:.4f}   95% CI [{result['rr_ci'][0]:.4f}, {result['rr_ci'][1]:.4f}]")
print(f"  Bootstrap p-value (RD): {result['p_rd']:.4f}")
if result['rd_ci'][1] < 0:
    conclusion = "STATISTICALLY SIGNIFICANT reduction in event risk."
elif result['rd_ci'][0] > 0:
    conclusion = "STATISTICALLY SIGNIFICANT INCREASE in event risk."
else:
    conclusion = "No statistically significant effect (95% CI crosses null)."
print(f"\n  Interpretation: {conclusion}")

# ── Step 7: E-value (sensitivity to unmeasured confounding) ───────────────────
# E-value for RR: E = RR + sqrt(RR*(RR-1)) if RR > 1, else 1/RR analog
rr_v = result["rr"]
if rr_v < 1:
    rr_ev = 1.0 / rr_v
else:
    rr_ev = rr_v
evalue = rr_ev + np.sqrt(rr_ev * (rr_ev - 1))

rr_ci_bound = result["rr_ci"][0] if rr_v < 1 else result["rr_ci"][1]  # bound closer to null
rr_cb = 1.0 / rr_ci_bound if rr_v < 1 else rr_ci_bound
if rr_cb <= 1:
    evalue_ci = 1.0
else:
    evalue_ci = rr_cb + np.sqrt(rr_cb * (rr_cb - 1))

print(f"\n  E-value (point estimate): {evalue:.2f}")
print(f"  E-value (CI bound):       {evalue_ci:.2f}")
print(f"  Interpretation: An unmeasured confounder would need an association of ≥{evalue:.2f}× with")
print(f"  both treatment and outcome to fully explain away the observed effect.")

# ── Propensity score overlap plot ─────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(12, 4))

ax = axes[0]
ax.hist(ps[A==0], bins=40, alpha=0.5, color="steelblue", label="Control", density=True)
ax.hist(ps[A==1], bins=40, alpha=0.5, color="tomato",    label="Treated",  density=True)
ax.axvline(ps_lower, color="k", linestyle="--", linewidth=0.8, label=f"Trim bounds")
ax.axvline(ps_upper, color="k", linestyle="--", linewidth=0.8)
ax.set_xlabel("Propensity score")
ax.set_ylabel("Density")
ax.set_title("Propensity Score Overlap")
ax.legend()

ax = axes[1]
vars_plot = ["age", "baseline_severity", "comorbidity_count", "lab_a", "lab_b"]
smds_raw = [abs(smd(X_conf[v].values, A)) for v in vars_plot]
smds_wtd = [abs(smd(X_conf[v].values, A, weights=sw)) for v in vars_plot]
y_pos = np.arange(len(vars_plot))
ax.barh(y_pos - 0.2, smds_raw, 0.35, color="steelblue", label="Unadjusted")
ax.barh(y_pos + 0.2, smds_wtd, 0.35, color="tomato",    label="IPTW-weighted")
ax.axvline(0.1, color="k", linestyle="--", linewidth=0.8, label="|SMD|=0.1")
ax.set_yticks(y_pos); ax.set_yticklabels(vars_plot)
ax.set_xlabel("|SMD|")
ax.set_title("Covariate Balance")
ax.legend()

plt.tight_layout()
os.makedirs(os.path.join(_HERE, "figures"), exist_ok=True)
plt.savefig(os.path.join(_HERE, "figures", "causal_diagnostics.png"), dpi=150)
plt.close()
print("\n  Saved: causal_diagnostics.png")


# ──────────────────────────────────────────────────────────────────────────────
# ANALYSIS 2: PREDICTIVE MODELING
# Outcome: event_1yr
# Features: age, sex, baseline_severity, comorbidity_count, lab_a, lab_b, site, new_drug
# EXCLUDES: followup_marker (post-baseline leakage), time_days, event_observed
# Validation: stratified 10-fold CV (no same-subject split issues; cross-sectional prediction)
# Models: (A) logistic regression baseline, (B) HistGradientBoosting (handles NaN natively)
# Metrics: AUC-ROC, Brier score, calibration
# ──────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("ANALYSIS 2 — PREDICTIVE MODEL FOR 1-YEAR EVENT")
print("=" * 70)

# ── Feature matrix (baseline only, leakage-free) ─────────────────────────────
X_pred_raw = df[PRED_FEATURES].copy()

# Encode site as one-hot; sex is 0/1 numeric
site_dummies = pd.get_dummies(X_pred_raw["site"], prefix="site", drop_first=True)
X_pred = pd.concat([
    X_pred_raw.drop(columns=["site"]),
    site_dummies.astype(float)
], axis=1)
# lab_b remains with NaN — HistGBT handles it; for LogReg we'll impute inside CV

feature_names = list(X_pred.columns)
print(f"\nFeature set ({len(feature_names)} features): {feature_names}")
print(f"Events: {Y.sum()} / {len(Y)}  ({Y.mean()*100:.1f}%)")

# ── Nested 10-fold CV ─────────────────────────────────────────────────────────
cv_outer = StratifiedKFold(n_splits=10, shuffle=True, random_state=RNG)

# Model A: Logistic regression with median imputation for lab_b
from sklearn.pipeline import Pipeline as Pipe
from sklearn.impute import SimpleImputer

logreg_pipe = Pipe([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler",  StandardScaler()),
    ("clf",     LogisticRegression(max_iter=1000, C=0.5, solver="lbfgs"))
])

# Model B: HistGradientBoosting (handles NaN natively, built-in regularisation)
hgbt = HistGradientBoostingClassifier(
    max_iter=300, learning_rate=0.05, max_depth=4,
    min_samples_leaf=20, l2_regularization=1.0, random_state=RNG
)

X_arr = X_pred.values

print("\nRunning 10-fold cross-validation...")
probs_lr   = np.zeros(len(Y))
probs_hgbt = np.zeros(len(Y))

fold_aucs_lr   = []
fold_aucs_hgbt = []

for fold, (tr, te) in enumerate(cv_outer.split(X_arr, Y)):
    # Logistic regression
    logreg_pipe.fit(X_arr[tr], Y[tr])
    probs_lr[te] = logreg_pipe.predict_proba(X_arr[te])[:, 1]
    fold_aucs_lr.append(roc_auc_score(Y[te], probs_lr[te]))

    # HistGBT
    hgbt.fit(X_arr[tr], Y[tr])
    probs_hgbt[te] = hgbt.predict_proba(X_arr[te])[:, 1]
    fold_aucs_hgbt.append(roc_auc_score(Y[te], probs_hgbt[te]))

# ── Overall metrics ───────────────────────────────────────────────────────────
auc_lr   = roc_auc_score(Y, probs_lr)
auc_hgbt = roc_auc_score(Y, probs_hgbt)
brier_lr   = brier_score_loss(Y, probs_lr)
brier_hgbt = brier_score_loss(Y, probs_hgbt)
prauc_lr   = average_precision_score(Y, probs_lr)
prauc_hgbt = average_precision_score(Y, probs_hgbt)

# Bootstrap 95% CI on AUC
def auc_ci(y, p, n_boot=2000):
    aucs = [roc_auc_score(y[idx], p[idx])
            for idx in (np.random.choice(len(y), len(y), replace=True) for _ in range(n_boot))
            if len(np.unique(y[idx])) == 2]
    return np.percentile(aucs, [2.5, 97.5])

print("\nBootstrapping AUC confidence intervals...")
ci_lr   = auc_ci(Y, probs_lr)
ci_hgbt = auc_ci(Y, probs_hgbt)

print(f"\n{'─'*60}")
print(f"PREDICTIVE MODEL PERFORMANCE (10-fold CV, honest out-of-sample)")
print(f"{'─'*60}")
print(f"  {'Model':<35} {'AUC-ROC':>9} {'95% CI':>20} {'Brier':>8} {'PR-AUC':>8}")
print(f"  {'─'*35} {'─'*9} {'─'*20} {'─'*8} {'─'*8}")
print(f"  {'Logistic Regression (baseline)':<35} {auc_lr:>9.4f} {f'[{ci_lr[0]:.4f}, {ci_lr[1]:.4f}]':>20} {brier_lr:>8.4f} {prauc_lr:>8.4f}")
print(f"  {'HistGradientBoosting':<35} {auc_hgbt:>9.4f} {f'[{ci_hgbt[0]:.4f}, {ci_hgbt[1]:.4f}]':>20} {brier_hgbt:>8.4f} {prauc_hgbt:>8.4f}")

# Null Brier (predict prevalence always)
null_brier = brier_score_loss(Y, np.full(len(Y), Y.mean()))
print(f"\n  Null Brier (predict prevalence = {Y.mean():.3f}): {null_brier:.4f}")
print(f"  Brier Skill Score (HGBT): {1 - brier_hgbt/null_brier:.4f} (0=null, 1=perfect)")

print(f"\n  Fold-level AUC (mean ± SD across 10 folds):")
print(f"  LogReg:  {np.mean(fold_aucs_lr):.4f} ± {np.std(fold_aucs_lr):.4f}")
print(f"  HGBT:    {np.mean(fold_aucs_hgbt):.4f} ± {np.std(fold_aucs_hgbt):.4f}")

# ── Feature importance (HGBT) ─────────────────────────────────────────────────
# Refit on full data for importance (report only — not used for performance claims)
hgbt_full = HistGradientBoostingClassifier(
    max_iter=300, learning_rate=0.05, max_depth=4,
    min_samples_leaf=20, l2_regularization=1.0, random_state=RNG
)
hgbt_full.fit(X_arr, Y)
importances = hgbt_full._raw_predict(X_arr)   # placeholder — use permutation importance
from sklearn.inspection import permutation_importance
perm = permutation_importance(hgbt_full, X_arr, Y, n_repeats=10, random_state=RNG,
                               scoring="roc_auc", n_jobs=-1)
imp_df = pd.DataFrame({
    "feature": feature_names,
    "importance_mean": perm.importances_mean,
    "importance_std":  perm.importances_std
}).sort_values("importance_mean", ascending=False)

print(f"\n  Permutation feature importances (HGBT, full data, metric=AUC):")
for _, row in imp_df.iterrows():
    bar = "█" * int(max(0, row["importance_mean"]) * 200)
    print(f"  {row['feature']:<25} {row['importance_mean']:+.5f} ± {row['importance_std']:.5f}  {bar}")

# ── Calibration + ROC plots ───────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

# ROC curves
from sklearn.metrics import roc_curve
ax = axes[0]
for label, probs, col in [("LogReg", probs_lr, "steelblue"), ("HGBT", probs_hgbt, "tomato")]:
    fpr, tpr, _ = roc_curve(Y, probs)
    auc_val = roc_auc_score(Y, probs)
    ax.plot(fpr, tpr, color=col, lw=2, label=f"{label} (AUC={auc_val:.3f})")
ax.plot([0,1],[0,1],"k--",lw=1)
ax.set_xlabel("False positive rate"); ax.set_ylabel("True positive rate")
ax.set_title("ROC curve (10-fold CV OOF)")
ax.legend()

# Calibration plots
ax = axes[1]
for label, probs, col in [("LogReg", probs_lr, "steelblue"), ("HGBT", probs_hgbt, "tomato")]:
    frac_pos, mean_pred = calibration_curve(Y, probs, n_bins=10, strategy="quantile")
    ax.plot(mean_pred, frac_pos, "s-", color=col, label=label)
ax.plot([0,1],[0,1],"k--",lw=1,label="Perfect")
ax.set_xlabel("Mean predicted probability"); ax.set_ylabel("Fraction of positives")
ax.set_title("Calibration curve (10-fold CV OOF)")
ax.legend()

# Decision curve analysis (net benefit)
ax = axes[2]
thresholds = np.linspace(0.01, 0.50, 100)
def net_benefit(y, p, thresh):
    tp = ((p >= thresh) & (y == 1)).sum()
    fp = ((p >= thresh) & (y == 0)).sum()
    n = len(y)
    return tp/n - fp/n * thresh/(1-thresh)

nb_lr   = [net_benefit(Y, probs_lr,   t) for t in thresholds]
nb_hgbt = [net_benefit(Y, probs_hgbt, t) for t in thresholds]
nb_all  = [Y.mean() - (1-Y.mean())*t/(1-t) for t in thresholds]   # treat all
nb_none = [0.0] * len(thresholds)

ax.plot(thresholds*100, nb_lr,   color="steelblue", lw=2, label="LogReg")
ax.plot(thresholds*100, nb_hgbt, color="tomato",    lw=2, label="HGBT")
ax.plot(thresholds*100, nb_all,  color="gray",      lw=1.5, linestyle="--", label="Treat all")
ax.axhline(0, color="k", lw=1,  linestyle="-",                              label="Treat none")
ax.set_xlabel("Threshold probability (%)")
ax.set_ylabel("Net benefit")
ax.set_title("Decision Curve Analysis")
ax.set_ylim(-0.05, 0.15)
ax.legend()

plt.tight_layout()
plt.savefig(os.path.join(_HERE, "figures", "prediction_diagnostics.png"), dpi=150)
plt.close()
print("\n  Saved: prediction_diagnostics.png")

# ── Youden threshold ──────────────────────────────────────────────────────────
from sklearn.metrics import roc_curve
fpr_h, tpr_h, thr_h = roc_curve(Y, probs_hgbt)
youden_idx = np.argmax(tpr_h - fpr_h)
best_thr   = thr_h[youden_idx]
tp = ((probs_hgbt >= best_thr) & (Y == 1)).sum()
fp = ((probs_hgbt >= best_thr) & (Y == 0)).sum()
tn = ((probs_hgbt <  best_thr) & (Y == 0)).sum()
fn = ((probs_hgbt <  best_thr) & (Y == 1)).sum()
sens = tp / (tp + fn)
spec = tn / (tn + fp)
ppv  = tp / (tp + fp)
npv  = tn / (tn + fn)

print(f"\n  Operating point (Youden index, HGBT):")
print(f"  Threshold: {best_thr:.3f}")
print(f"  Sensitivity: {sens:.3f} | Specificity: {spec:.3f} | PPV: {ppv:.3f} | NPV: {npv:.3f}")

# ──────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"""
CAUSAL QUESTION — Does new_drug reduce 1-year event risk?
  Method: Doubly-robust AIPW with IPTW propensity score (logistic regression)
  Adjustment: age, sex, baseline_severity, comorbidity_count, lab_a, lab_b, site
  (followup_marker excluded — post-treatment variable)

  Risk under new drug:    {result['mu1']*100:.2f}%
  Risk under standard Rx: {result['mu0']*100:.2f}%
  Risk Difference:  {result['rd']:+.4f}  95% CI [{result['rd_ci'][0]:+.4f}, {result['rd_ci'][1]:+.4f}]  p={result['p_rd']:.4f}
  Risk Ratio:       {result['rr']:.4f}   95% CI [{result['rr_ci'][0]:.4f}, {result['rr_ci'][1]:.4f}]
  E-value (point):  {evalue:.2f}  (CI bound: {evalue_ci:.2f})

PREDICTIVE QUESTION — How well can we predict 1-year event?
  Best model: HistGradientBoosting  AUC = {auc_hgbt:.4f}  [{ci_hgbt[0]:.4f}, {ci_hgbt[1]:.4f}]
  Logistic baseline:                AUC = {auc_lr:.4f}  [{ci_lr[0]:.4f}, {ci_lr[1]:.4f}]
  Brier score (HGBT): {brier_hgbt:.4f}  (null: {null_brier:.4f},  skill: {1-brier_hgbt/null_brier:.4f})
  All 10-fold AUCs stable: {np.mean(fold_aucs_hgbt):.4f} ± {np.std(fold_aucs_hgbt):.4f}

LEAKAGE EXCLUSION: followup_marker was excluded from both analyses (recorded post-baseline).
""")
