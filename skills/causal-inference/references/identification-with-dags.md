# Identification with DAGs and the Target Trial

Before any estimator, settle *identification*: would this analysis recover the causal effect if we
had infinite data? That is a question about assumptions and structure, not about the model.

## 1. Emulate a target trial

Specify the (hypothetical) randomized trial you wish you could run, then emulate it in the data.
This forces the decisions that prevent the classic biases.

| Protocol element | Decision to make |
|---|---|
| Eligibility | who is in the population, assessed at baseline only |
| Treatment strategies | the exposure contrast (e.g. initiate A vs initiate B) |
| **Time zero** | the moment eligibility, treatment assignment, and follow-up all begin — *aligned* |
| Outcome | precisely defined, ascertained the same way in both arms |
| Causal contrast | ITT-analogue vs per-protocol; ATE vs ATT; scale (RD/RR/HR) |
| Follow-up & censoring | start at time zero, censoring mechanism stated |

**Immortal time bias** comes from defining exposure using information after time zero (so the
exposed must "survive" to be classified). **Prevalent-user / selection bias** comes from
enrolling people already on treatment. Align time zero and use new-user designs to avoid both.

## 2. Draw the DAG

A DAG encodes which variables cause which. From it you can read off what to adjust for.

- **Confounder:** a common cause of exposure and outcome (a backdoor path). **Adjust for it.**
- **Mediator:** on the causal path exposure → M → outcome. **Do not adjust** (unless decomposing
  direct/indirect effects on purpose) — it blocks part of the effect you want.
- **Collider:** a common effect of two variables. **Do not condition on it** — conditioning opens
  a spurious path (selection / collider-stratification bias). Selecting your sample on a collider
  has the same effect.
- **Instrument / competing exposure:** adjusting for an instrument can amplify bias.

The **backdoor criterion**: an adjustment set is sufficient if it blocks every backdoor path from
exposure to outcome and contains no descendants of the exposure.

```r
# R: derive a minimal sufficient adjustment set
library(dagitty)
g <- dagitty('dag {
  exposure -> outcome
  age -> exposure
  age -> outcome
  severity -> exposure
  severity -> outcome
  exposure -> biomarker -> outcome   # biomarker is a MEDIATOR: do not adjust
}')
adjustmentSets(g, exposure = "exposure", outcome = "outcome")  # -> { age, severity }
```

```python
# Python: same idea via dowhy / pgmpy or networkx; or specify the adjustment set from the DAG
# and validate with dowhy's identification step.
from dowhy import CausalModel
model = CausalModel(data=df, treatment="exposure", outcome="outcome",
                    common_causes=["age", "severity"])  # confounders from the DAG, not all columns
estimand = model.identify_effect()
print(estimand)
```

## 3. Positivity / overlap

Identification also requires **positivity**: within every confounder stratum, both treatments
occur with non-zero probability. Check the propensity-score overlap between groups; where it
fails, you can only estimate an effect in the region of overlap (restrict/trim, and say so).

## 4. The assumptions, named

For adjustment-based identification of a causal effect you are assuming:

1. **Exchangeability / no unmeasured confounding** — the adjustment set closes all backdoor paths.
2. **Positivity** — overlap in treatment across covariate patterns.
3. **Consistency / well-defined intervention** — the exposure corresponds to a meaningful action.
4. **Correct temporal order** — confounders precede exposure; the outcome follows.
5. **No interference** — one unit's treatment doesn't affect another's outcome (often reasonable;
   not always, e.g. infectious disease).

Assumptions 1 and 2 are checkable only partially; that is why a sensitivity analysis is mandatory
(see `estimators-and-sensitivity.md`). Design-based strategies (DiD/IV/RD) trade assumption 1 for
a different, also-unverifiable assumption — choose the one most plausible in your setting and be
explicit about it.
