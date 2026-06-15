"""Generate ONE realistic clinical cohort with KNOWN injected ground truth, to drive an
end-to-end agent demo. Designed so a NAIVE analysis reaches the WRONG conclusion: the new
drug is truly protective (true conditional OR = 0.70), but confounding by indication (sicker
patients preferentially get it) masks/ reverses that in an unadjusted comparison. Only the full
workflow (design -> data -> causal adjustment -> missing data -> analysis -> critique -> report)
recovers the truth. A separate leakage feature tests the prediction sub-task.

The agent NEVER sees this script or the ground-truth file — only cohort.csv + DATA_DICTIONARY.md.
"""
import os, numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score

HERE = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(424242)
sig = lambda x: 1/(1+np.exp(-x))
n = 3000

site = rng.choice(["North","Central","South"], n, p=[.4,.35,.25])
age = np.clip(rng.normal(64,11,n), 30, 95)
sex = rng.integers(0,2,n)
severity = rng.normal(0,1,n)                          # baseline severity (confounder)
comorbidity = rng.poisson(2, n)
lab1 = rng.normal(0,1,n)
lab2 = rng.normal(0,1,n)

# confounding by indication: sicker (higher severity/comorbidity) more likely to get the NEW drug
p_treat = sig(-0.3 + 0.95*severity + 0.18*(comorbidity-2) + 0.15*lab1)
treatment = rng.binomial(1, p_treat)                  # 1 = new drug, 0 = standard care

# TRUE outcome model: new drug is PROTECTIVE (log OR = log(0.70)); severity strongly harmful
lp = -0.6 + 0.85*severity + 0.15*(comorbidity-2) + 0.30*lab1 + np.log(0.70)*treatment
event_1yr = rng.binomial(1, sig(lp))                  # 1 = death/MACE within 1 year

# survival flavor: time-to-event (days) ~ Weibull-ish driven by the same risk; censor at 365
rate = np.exp((lp - lp.mean())*0.8) * 0.0016
t_event = rng.exponential(1/np.clip(rate,1e-5,None))
time_days = np.minimum(t_event, 365).round(0)
event_observed = ((t_event<=365) & (event_1yr==1)).astype(int)

# LEAKAGE feature: a marker recorded DURING follow-up (after baseline), tied to the outcome
post_baseline_marker = (rng.normal(np.where(event_1yr==1, 1.4, -0.4), 0.7)).round(3)

# MAR missingness: lab2 missing more often when severity is high (depends on OBSERVED severity)
miss = rng.binomial(1, sig(-1.6 + 0.8*severity))==1
lab2_obs = lab2.copy().astype(object); lab2_obs[miss] = np.nan

df = pd.DataFrame({
    "patient_id": np.arange(1,n+1), "site": site, "age": age.round(1), "sex": sex,
    "baseline_severity": severity.round(3), "comorbidity_count": comorbidity,
    "lab_a": lab1.round(3), "lab_b": lab2_obs,
    "new_drug": treatment, "followup_marker": post_baseline_marker,
    "time_days": time_days.astype(int), "event_observed": event_observed, "event_1yr": event_1yr,
})
os.makedirs(HERE, exist_ok=True)
df.to_csv(f"{HERE}/cohort.csv", index=False)

# ---- realized ground truth (what a correct analysis should find) ----
dd = df.copy(); dd["lab_b"] = pd.to_numeric(dd["lab_b"], errors="coerce")
cc = dd.dropna(subset=["lab_b"])
def OR(cols):
    m = LogisticRegression(penalty=None, max_iter=3000).fit(cc[cols], cc["event_1yr"]);
    return float(np.exp(m.coef_[0][list(cols).index("new_drug")]))
naive = OR(["new_drug"])
adj = OR(["new_drug","baseline_severity","comorbidity_count","lab_a","age"])
legit = ["age","baseline_severity","comorbidity_count","lab_a"]
Xtr,Xte,ytr,yte = train_test_split(cc, cc["event_1yr"], test_size=.3, random_state=1, stratify=cc["event_1yr"])
auc_legit = roc_auc_score(yte, LogisticRegression(max_iter=3000).fit(Xtr[legit],ytr).predict_proba(Xte[legit])[:,1])
auc_leak = roc_auc_score(yte, LogisticRegression(max_iter=3000).fit(Xtr[legit+["followup_marker"]],ytr).predict_proba(Xte[legit+["followup_marker"]])[:,1])
print(f"n={n}  event rate={df.event_1yr.mean():.3f}  treated={df.new_drug.mean():.3f}  lab_b missing={miss.mean():.3f}")
print(f"CAUSAL  TRUE OR(new_drug)=0.70 | NAIVE OR={naive:.2f}  ADJUSTED OR={adj:.2f}")
print(f"PREDICT legit AUC={auc_legit:.2f}  with-leak(followup_marker) AUC={auc_leak:.2f}")
