# Real transcripts — what the skill actually does, per use case

These are **raw, unedited** outputs from a skill-equipped agent (**Claude Code**, headless
`claude -p`, model **Sonnet** — mid-tier) answering questions five different kinds of user would
actually bring. We publish them so you can judge the suite on *your* kind of problem instead of
taking the pitch on faith. Each `.txt` is the verbatim run; the exact prompt is below — rerun it
against your own install and compare.

> Different model behind your agent → different prose, but the methodology the skills enforce
> (estimand, leakage, confounding, missingness, sensitivity, honest reporting) is what to look for.

## [`ps-critique.txt`](./ps-critique.txt) — senior biostatistician critiques a propensity-score plan
**Prompt:** *"Critique this proposed analysis. We will compare anticoagulant X vs warfarin for stroke
in AF patients using propensity-score matching, adjusting for medication adherence and INR measured
during follow-up, and defining exposure as 'ever used X during the study period.' Identify the
estimand, the design flaws, the diagnostics you'd require, and the fixes."*
**It caught (unprompted):** the *"ever used"* exposure → **immortal-time / prevalent-user bias**;
**adjusting for post-baseline adherence and INR → conditioning on mediators/colliders**; the
**undefined estimand** (→ a defined ITT contrast); demanded **baseline CHA₂DS₂-VASc / HAS-BLED** in
the PS; required **balance, overlap, and an E-value**; flagged channeling bias and recommended
pharmacoepidemiologist review for regulatory use. *(skills: causal-inference, method-evaluation.)*

## [`naive-triage.txt`](./naive-triage.txt) — non-statistician asks "is this OK to submit?"
**Prompt:** *"I did a median split on my biomarker, ran a t-test, got p=0.04, wrote 'biomarker X
causes worse outcomes', and excluded the 23% of patients with missing data. Is this OK to submit?"*
**It caught:** **three compounding fatal problems** — dichotomizing a continuous biomarker (median
split), **causal language from an association**, and **complete-case exclusion of 23%** — each with
the established fix, prioritized. *(skills: statistical-analysis, causal-inference, missing-data,
reporting-and-reproducibility, method-evaluation.)*

## [`clinical-plan.txt`](./clinical-plan.txt) — clinician/researcher wants an analysis plan
**Prompt:** *"I have a retrospective sepsis cohort and want to estimate the effect of early
hydrocortisone on 28-day mortality. Give me an analysis plan and tell me what reviewers will attack."*
**It produced:** a **target-trial-emulation** plan with explicit **time-zero / immortal-time**
handling, confounding-by-indication control, **positivity/overlap** checks, a **missing-lab** plan,
**E-value** sensitivity, pre-specified analyses, STROBE alignment — and named *"the two attacks that
can sink the paper."* *(skills: study-design-and-power, causal-inference, missing-data, reporting.)*

## [`routing.txt`](./routing.txt) — the orchestrator routing eight requests
Raw log of the `biostatistics` orchestrator routing eight different asks to the right specialist,
each with a one-line reason (e.g. *"observational EHR data with a causal verb → `causal-inference`:
needs a DAG and confounding adjustment before any estimate is credible"*). Rerun the prompts in
[`../validation/routing-check.md`](../validation/routing-check.md) and compare.

## Also
- [`../demo/`](../demo/) — the flagship: one naive prompt → full pipeline → recovers a hidden truth
  on data with injected ground truth (covers the ML/prediction user too).
- [Reviewer evidence checklist](../../skills/reporting-and-reproducibility/references/reviewer-evidence-checklist.md)
  — what a manuscript that used the suite should be able to *show* (for editors/reviewers).
- [`../validation/routing-check.md`](../validation/routing-check.md) — rerun the routing & guard-rail probes yourself.
