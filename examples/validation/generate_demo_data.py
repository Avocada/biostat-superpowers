#!/usr/bin/env python3
"""Generate two synthetic datasets with KNOWN ground truth, to demo and stress-test the suite.

Run:
    python3 generate_demo_data.py        # writes the two CSVs next to this script

Requires: numpy, pandas, scikit-learn. Each dataset hides a classic, fatal mistake; a disciplined
biomedical statistician (or this skill suite) should recover the truth and catch the trap.
"""
import os
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score

HERE = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(20260615)
sig = lambda x: 1 / (1 + np.exp(-x))

# ---- DS1: confounded observational cohort; TRUE causal OR(Drug A) = 1.00 (null) ----
n = 5000
severity = rng.normal(0, 1, n)                                  # baseline confounder
age = rng.normal(65, 10, n)
sex = rng.integers(0, 2, n)
A = rng.binomial(1, sig(-0.2 + 1.0 * severity + 0.01 * (age - 65)))   # sicker -> more likely treated
Y = rng.binomial(1, sig(-1.0 + 1.5 * severity + 0.02 * (age - 65) + 0.0 * A))  # true log-OR(A) = 0
pd.DataFrame({"patient_id": np.arange(1, n + 1), "age": age.round(1), "sex": sex,
             "severity_score": severity.round(3), "treatment_A": A, "death_1yr": Y}
            ).to_csv(os.path.join(HERE, "confounding_cohort.csv"), index=False)

def logor(df, cols):
    m = LogisticRegression(penalty=None, max_iter=2000).fit(df[cols], df["death_1yr"])
    return m.coef_[0][0]
df1 = pd.read_csv(os.path.join(HERE, "confounding_cohort.csv"))
naive = logor(df1, ["treatment_A"])
adj = logor(df1, ["treatment_A", "severity_score", "age"])
print(f"DS1 confounding  naive OR(A)={np.exp(naive):.2f}  adjusted OR(A)={np.exp(adj):.2f}  TRUTH OR=1.00")

# ---- DS2: prediction with a temporal-leakage feature ----
n = 5000
age2 = rng.normal(68, 12, n); n_prior = rng.poisson(1.5, n)
comorbidity = rng.normal(0, 1, n); lab1 = rng.normal(0, 1, n); lab2 = rng.normal(0, 1, n)
readmit = rng.binomial(1, sig(-1.2 + 0.02 * (age2 - 68) + 0.35 * n_prior + 0.45 * comorbidity + 0.25 * lab1))
# leakage: follow-up visits in the 90 days AFTER discharge -> future info, not known at prediction time
followup_visits_90d = rng.poisson(np.where(readmit == 1, 0.3, 3.0)) + rng.binomial(1, 0.05, n)
pd.DataFrame({"patient_id": np.arange(1, n + 1), "age": age2.round(1), "n_prior_admissions": n_prior,
             "comorbidity_index": comorbidity.round(3), "lab1": lab1.round(3), "lab2": lab2.round(3),
             "followup_visits_90d": followup_visits_90d, "readmit_30d": readmit}
            ).to_csv(os.path.join(HERE, "readmission_prediction.csv"), index=False)

df2 = pd.read_csv(os.path.join(HERE, "readmission_prediction.csv"))
legit = ["age", "n_prior_admissions", "comorbidity_index", "lab1", "lab2"]
Xtr, Xte, ytr, yte = train_test_split(df2, df2["readmit_30d"], test_size=0.3, random_state=1, stratify=df2["readmit_30d"])
auc_legit = roc_auc_score(yte, LogisticRegression(max_iter=2000).fit(Xtr[legit], ytr).predict_proba(Xte[legit])[:, 1])
auc_leak = roc_auc_score(yte, LogisticRegression(max_iter=2000).fit(Xtr[legit + ["followup_visits_90d"]], ytr).predict_proba(Xte[legit + ["followup_visits_90d"]])[:, 1])
print(f"DS2 leakage      legit-only AUC={auc_legit:.2f}  with-leaky-feature AUC={auc_leak:.2f}  (leaky feature is post-outcome)")
