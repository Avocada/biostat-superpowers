# Study Designs

Pick the design from the question, the feasibility of randomization, and the time structure of
exposure and outcome. The design fixes which effects are identifiable and which biases threaten it.

## Experimental designs (randomization available)

- **Parallel-group RCT** — randomize subjects to arms; the comparator is concurrent. Randomization
  makes the groups exchangeable in expectation, so the difference estimates a causal effect.
- **Cluster RCT** — randomize groups (clinics, wards, villages). Outcomes within a cluster are
  correlated (ICC); the design effect inflates the required sample size.
- **Crossover** — each subject receives both treatments in sequence; each is their own control.
  Powerful for chronic, stable conditions; threatened by carryover (use washout) and period effects.
- **Factorial** — test two or more interventions simultaneously; efficient if no interaction.
- **Stepped-wedge** — clusters cross from control to intervention at randomized times; useful when
  rollout is unavoidable, but confounded with secular time trends if not modeled.
- **Adaptive / group-sequential** — pre-planned interim analyses with alpha-spending; can stop
  early for efficacy/futility. Requires pre-specified rules (route the multiplicity to
  `method-evaluation`).

## Observational designs (randomization not possible/ethical)

- **Prospective cohort** — define exposure at baseline, follow forward for outcomes. Estimates
  incidence and relative risk / hazard. Threats: confounding, loss to follow-up.
- **Retrospective cohort** — same logic, reconstructed from existing records (EHR/claims/registry).
  Threats: confounding, data quality, immortal time, measurement.
- **Case-control** — sample on the outcome (cases vs controls), look back at exposure. Efficient
  for rare outcomes; estimates an odds ratio (≈ RR when the outcome is rare). Threats: control
  selection, recall bias.
- **Nested case-control / case-cohort** — efficient sampling within a defined cohort; preserves
  the cohort's time structure while reducing measurement cost.
- **Cross-sectional** — exposure and outcome measured at one time. Estimates prevalence and
  association; cannot establish temporality (reverse causation).
- **Case-crossover / self-controlled case series** — compare exposure in case vs control time
  windows within the same person; controls all fixed confounders by design. For transient
  exposures and acute outcomes.

## New-user (active-comparator) design

For observational drug/treatment questions, prefer a **new-user, active-comparator** design:
enroll people initiating treatment A vs initiating a clinically relevant comparator B at time
zero. This aligns time zero, avoids prevalent-user and immortal-time bias, and mirrors a target
trial. Hand the identification details to `causal-inference`.

## Diagnostic and prognostic studies

- **Diagnostic accuracy** — compare an index test against a reference standard; report
  sensitivity, specificity, predictive values, and ROC/AUC. Threats: spectrum bias, partial/
  differential verification. Report with STARD.
- **Prognostic / prediction model** — develop and validate a model predicting an outcome. Plan
  events-per-variable, and internal + external validation up front. Build it with
  `predictive-modeling` and report with TRIPOD.

## Choosing — quick logic

1. Can you randomize ethically and feasibly? → experimental.
2. Rare outcome? → case-control or cohort with long follow-up.
3. Transient exposure, acute outcome? → case-crossover.
4. Only one time point available? → cross-sectional (association only).
5. Observational but want a causal effect? → cohort with new-user/active-comparator design +
   `causal-inference`.
