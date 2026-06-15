#!/usr/bin/env python3
"""
Flagship demo — causal effect of Right Heart Catheterization (RHC) on 30-day mortality.

Real data: the SUPPORT / Connors et al. (1996, JAMA) right-heart-catheterization study —
5,735 ICU patients, a landmark observational dataset used for decades to teach propensity-score
methods. Public mirror: https://hbiostat.org/data/repo/rhc.csv

The question: does RHC *cause* higher mortality, or is the raw difference confounding by
indication (sicker patients are more likely to be catheterized)? This script is the analysis a
biostatistician — or an agent driving the `causal-inference` + `statistical-analysis` skills —
would run: a target-trial-style adjusted comparison with a propensity score, IPTW, covariate-
balance diagnostics, and an E-value for unmeasured confounding.

Run:  python3 rhc_causal.py          (needs: pandas, numpy, statsmodels, scikit-learn; fetches data)
"""
import numpy as np, pandas as pd, statsmodels.api as sm
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

URL = "https://hbiostat.org/data/repo/rhc.csv"
d = pd.read_csv(URL)
if d.columns[0].lower().startswith("unnamed") or d.columns[0] == "":
    d = d.drop(columns=d.columns[0])

# Treatment = received RHC within 24h; outcome = death within 30 days.
t = (d["swang1"] == "RHC").astype(int).values
y = (d["dth30"] == "Yes").astype(int).values

# Adjustment set = the baseline covariates (demographics, diagnoses, comorbidities, physiology,
# baseline labs and prognosis scores). We exclude only the treatment, outcomes, dates, and IDs —
# never anything measured after baseline (no post-treatment variables, no colliders by timing).
drop = [c for c in ["swang1", "death", "dth30", "t3d30", "dthdte", "lstctdte",
                    "dschdte", "sadmdte", "ptid"] if c in d.columns]
X = pd.get_dummies(d.drop(columns=drop), drop_first=True, dummy_na=False)
X = X.apply(pd.to_numeric, errors="coerce").fillna(X.median(numeric_only=True)).fillna(0)
Xs = StandardScaler().fit_transform(X)

# 1) Propensity score P(RHC | baseline covariates) and stabilized IPTW weights.
ps = LogisticRegression(max_iter=5000, C=1.0).fit(Xs, t).predict_proba(Xs)[:, 1]
ps = np.clip(ps, 0.02, 0.98)                       # trim to the region of overlap
pt = t.mean()
w = np.where(t == 1, pt / ps, (1 - pt) / (1 - ps))

def risks(y, t, w=None):
    if w is None:
        return y[t == 1].mean(), y[t == 0].mean()
    return np.average(y[t == 1], weights=w[t == 1]), np.average(y[t == 0], weights=w[t == 0])

r1n, r0n = risks(y, t);            rr_naive = r1n / r0n
r1w, r0w = risks(y, t, w);         rr_iptw = r1w / r0w;  rd_iptw = r1w - r0w

# 2) Regression-adjusted (g-computation-style) odds ratio, all baseline covariates.
or_naive = np.exp(sm.Logit(y, sm.add_constant(t)).fit(disp=0).params[1])
or_adj = np.exp(sm.Logit(y, sm.add_constant(np.column_stack([t, Xs]))).fit(disp=0, maxiter=200).params[1])

# 3) Covariate balance: mean |standardized mean difference| before vs after weighting.
def smd(col, t, w=None):
    a, b = col[t == 1], col[t == 0]
    if w is None:
        m1, m0, v1, v0 = a.mean(), b.mean(), a.var(), b.var()
    else:
        w1, w0 = w[t == 1], w[t == 0]
        m1, m0 = np.average(a, weights=w1), np.average(b, weights=w0)
        v1 = np.average((a - m1) ** 2, weights=w1); v0 = np.average((b - m0) ** 2, weights=w0)
    s = np.sqrt((v1 + v0) / 2)
    return abs(m1 - m0) / s if s > 0 else 0.0
smd_before = np.mean([smd(Xs[:, j], t) for j in range(Xs.shape[1])])
smd_after = np.mean([smd(Xs[:, j], t, w) for j in range(Xs.shape[1])])

# 4) E-value: how strong an unmeasured confounder would have to be to explain away the IPTW RR.
rrstar = max(rr_iptw, 1 / rr_iptw)
evalue = rrstar + np.sqrt(rrstar * (rrstar - 1))

print(f"RHC causal demo  |  n={len(y)}, RHC={t.sum()}, covariates={X.shape[1]}, 30-day death rate={y.mean():.3f}\n")
print(f"  NAIVE      risk ratio = {rr_naive:.2f}   (odds ratio {or_naive:.2f})   <- looks like RHC is harmful")
print(f"  IPTW       risk ratio = {rr_iptw:.2f}   risk difference = {rd_iptw*100:+.1f} percentage points")
print(f"  REG-ADJ    odds ratio = {or_adj:.2f}")
print(f"  BALANCE    mean |SMD| {smd_before:.3f} (before)  ->  {smd_after:.3f} (after weighting)")
print(f"  E-VALUE    = {evalue:.2f}   (an unmeasured confounder would need RR~{evalue:.1f} with BOTH")
print( "             RHC and death to fully explain the association away)\n")
print("  Conclusion: even after adjusting for ~50 baseline covariates and checking balance, RHC is")
print("  associated with higher 30-day mortality — consistent with Connors et al. (1996). The")
print("  estimate is causal ONLY under no-unmeasured-confounding + positivity; the E-value says how")
print("  fragile that claim is. Report it as such, not as proof.")
