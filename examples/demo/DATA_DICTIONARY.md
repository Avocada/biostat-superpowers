# Data dictionary — `cohort.csv`

A de-identified observational cohort from routine care (n = 3000). Two research goals:

1. **Causal:** does starting the **new drug** reduce the risk of a 1-year event (death/MACE) vs standard care?
2. **Prediction:** build a model to **predict the 1-year event**, and report the AUC to expect in practice.

| column | meaning | when recorded |
|---|---|---|
| patient_id | identifier | — |
| site | care site (North/Central/South) | baseline |
| age | years | baseline |
| sex | 0/1 | baseline |
| baseline_severity | disease-severity index | baseline (before treatment) |
| comorbidity_count | number of comorbidities | baseline |
| lab_a | laboratory value A | baseline |
| lab_b | laboratory value B (some values missing) | baseline |
| new_drug | 1 = started new drug, 0 = standard care | baseline |
| followup_marker | a clinical marker recorded **during follow-up** | after baseline |
| time_days | follow-up time (days, censored at 365) | follow-up |
| event_observed | 1 = event observed during follow-up | follow-up |
| event_1yr | **primary outcome:** 1 = event within 1 year | by 1 year |
