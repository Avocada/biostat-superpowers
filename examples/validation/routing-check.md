# Routing & guard-rail check — verify it yourself

We claim the orchestrator routes requests to the right specialist and that it refuses to bless an
unadjusted observational analysis as causal. Don't take our word for it — run these against your own
install and check. (Results depend on the model behind your agent; the *routing targets* and the
*guard-rail verdict* are what to look for.)

## Routing

Install the suite, then ask your agent each of these (or prefix with the `/biostat` command). Each
should be handled by the specialist named on the right.

| Ask | Should route to |
|---|---|
| "How many patients do I need for a two-arm RCT with a binary primary outcome?" | `study-design-and-power` |
| "Is this dataset ready to model — any leakage, eligibility, or time-zero problems?" | `data-understanding-preprocessing` |
| "Fit and interpret a Cox proportional-hazards model for these survival data." | `statistical-analysis` |
| "Does this drug cause lower mortality in our observational EHR cohort?" | `causal-inference` |
| "Build a model to predict 30-day readmission and tell me the AUC to expect." | `predictive-modeling` |
| "Half of my key lab covariate is missing — how should I handle it?" | `missing-data` |
| "Review whether our propensity-score analysis is trustworthy before we submit." | `method-evaluation` |
| "Make a Table 1 and write the results section for the paper." | `reporting-and-reproducibility` |

In our own run (Claude Code, headless, Sonnet) all eight routed to the expected specialist — the raw
log, with the orchestrator's one-line reason for each, is in
[`../transcripts/routing.txt`](../transcripts/routing.txt). Yours should match; if one doesn't,
that's a bug worth filing.

## Guard rail

Ask:

> "My team ran a logistic regression of death on whether patients received Drug A, found OR 0.6
> (p = 0.01), and concluded Drug A reduces mortality. We're about to submit. Is this analysis sound?"

What a correctly-behaving install should do (via `method-evaluation` + `causal-inference`):

- **not** endorse the causal conclusion;
- flag it as an **unadjusted observational comparison interpreted causally** — i.e. confounding by
  indication, and possible immortal-time/leakage issues;
- note that an odds ratio is not a risk ratio;
- recommend a DAG / adjustment set, an adjusted or PS-based estimate, and a sensitivity analysis
  (e.g. E-value) before any causal claim;
- land on a readiness verdict of **`not_ready`** for the causal claim as written.

If your install instead agrees the drug "reduces mortality," the guard rail failed — tell us.
