---
name: study-design-and-power
description: >
  Use this skill at the START of a study — before data collection or analysis — to frame the
  research question, define the estimand, choose an appropriate study design, anticipate bias,
  and compute sample size / statistical power. It covers PICO/PECO question framing, the ICH E9(R1)
  estimand framework, the design taxonomy (RCT, cohort, case-control, cross-sectional,
  case-crossover, nested designs), randomization and blinding, sample-size and power calculations
  for means/proportions/survival/clustered designs (R and Python), bias anticipation, pre-
  registration, and choosing the right reporting guideline. Use it when someone asks "how many
  subjects do I need?", "what study design should I use?", "what's my power?", "how do I frame
  this question?", or "is this design appropriate for my question?".
---

# Study Design and Power

The cheapest place to fix a study is before it runs. A clear estimand, an appropriate design, and
an honest power calculation prevent the unfixable problems — an underpowered trial, a confounded
comparison, a question the data can never answer.

## Core workflow

1. **Frame the question (PICO / PECO).** Population, Intervention/Exposure, Comparator, Outcome —
   plus timeframe. Vague questions produce vague designs. Pin down the unit, the comparison, and
   when the outcome is measured.
2. **Define the estimand (ICH E9(R1) thinking).** State the population, the treatment/exposure
   contrast, the outcome (and its timing), how *intercurrent events* (treatment switching, death,
   rescue therapy) are handled, and the population-level summary (difference, ratio, hazard).
   The estimand is the precise target; the analysis comes later and must match it.
3. **Choose the design.** Match design to question and feasibility — see `references/study-designs.md`.
   Experimental (RCT, cluster-RCT, crossover, factorial, stepped-wedge) when randomization is
   possible and ethical; observational (cohort, case-control, cross-sectional, case-crossover,
   self-controlled) otherwise. For an observational *causal* question, design the analysis as a
   target-trial emulation and route identification to `causal-inference`.
4. **Anticipate bias up front.** Selection bias, confounding (what must be measured at baseline),
   measurement/misclassification, immortal time, loss to follow-up, and missing data. Design to
   prevent what you can (new-user design, blinding, blinded outcome assessment, pre-specified
   covariates) and plan to measure the rest.
5. **Plan randomization & blinding (experiments).** Allocation method (simple, block, stratified,
   minimization), allocation concealment, and who is blinded (participants, providers, assessors,
   analysts). These are the levers that make the estimand identifiable by design.
6. **Compute sample size / power.** Use `references/sample-size-and-power.md` (R `pwr`/`stats`,
   survival via Schoenfeld; Python `statsmodels`). Drive it from the *minimal clinically important
   effect*, not the effect you hope to see. State every assumption (event rate, SD, allocation
   ratio, dropout, ICC for clustered designs, multiplicity) and show sensitivity across plausible
   inputs. Report the design as power, α (one/two-sided), effect, and n.
7. **Pre-specify and pre-register.** Lock the primary estimand, primary analysis, and key
   secondary/subgroup analyses before seeing outcome data; everything else is exploratory. Point
   to a registry/protocol (ClinicalTrials.gov, OSF, PROSPERO for reviews).
8. **Pick the reporting guideline now** (it shapes what you must capture): CONSORT (RCT), STROBE
   (observational), TRIPOD (prediction models), PRISMA (systematic reviews/meta-analysis), SPIRIT
   (protocols), STARD (diagnostic accuracy). `reporting-and-reproducibility` uses this later.

## Design → typical effect measure → main threat

| Design | Estimates | Main threat to validity |
|---|---|---|
| RCT | causal effect (by randomization) | dropout, non-adherence, unblinding, underpowering |
| Cohort (prospective/retrospective) | incidence, RR/HR | confounding, loss to follow-up, immortal time |
| Case-control | odds ratio (≈ RR if rare) | selection & recall bias, control choice |
| Cross-sectional | prevalence, association | reverse causation, no temporality |
| Case-crossover / self-controlled | within-person effect | carryover, time-varying confounding |
| Diagnostic accuracy | sensitivity/specificity, ROC | spectrum bias, verification bias (use STARD) |

## Operating rules

- **Power is computed for a pre-specified effect, on the primary outcome, before data.**
  Post-hoc "observed power" is not informative — do not report it.
- **The estimand drives everything.** If you cannot state it in one sentence, the study is not
  ready to design.
- **Surface assumptions in the sample-size calc** and show how n moves if they are wrong.
- **Underpowered is a design flaw, not a footnote.** Say so when n is inadequate for the target
  effect, and give the n that would be adequate.
- For clustered/longitudinal designs, account for the design effect (ICC, cluster size) — ignoring
  it badly underpowers the study.

## Hand-offs

- Observational causal identification (DAGs, adjustment, target-trial estimator) → `causal-inference`.
- Turning the planned data into an analysis-ready table → `data-understanding-preprocessing`.
- Fitting the planned model → `statistical-analysis`.
- Predictive/prognostic model planning (events-per-variable, validation) → `predictive-modeling`.
- Reporting-guideline-aligned writeup and reproducibility → `reporting-and-reproducibility`.

## Output

Return a **Study Design & Power Plan**: (1) PICO/PECO question, (2) estimand (incl. intercurrent
events), (3) chosen design with rationale, (4) anticipated biases and design mitigations,
(5) randomization/blinding plan if experimental, (6) sample-size/power calculation with all
assumptions and a sensitivity table, (7) pre-registration & analysis-plan items, (8) selected
reporting guideline, (9) open questions for the investigator.
