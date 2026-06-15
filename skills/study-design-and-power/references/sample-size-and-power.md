# Sample Size and Power

Power the study for the **minimal clinically important effect**, on the **primary outcome**,
**before** collecting data. State every assumption and show how the required n changes if the
assumptions are wrong. Never report post-hoc "observed power".

The four quantities are linked — fix any three to solve for the fourth: effect size, α
(significance, usually two-sided 0.05), power (usually 0.80–0.90), and n.

## Two means (continuous outcome)

```r
# R
power.t.test(delta = 5, sd = 12, sig.level = 0.05, power = 0.80)        # n per group
library(pwr); pwr.t.test(d = 5/12, power = 0.80, sig.level = 0.05)      # standardized effect
```
```python
# Python
from statsmodels.stats.power import TTestIndPower
TTestIndPower().solve_power(effect_size=5/12, alpha=0.05, power=0.80, ratio=1.0)  # n per group
```

## Two proportions (binary outcome)

```r
power.prop.test(p1 = 0.30, p2 = 0.20, sig.level = 0.05, power = 0.80)   # n per group
```
```python
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize
es = proportion_effectsize(0.30, 0.20)
NormalIndPower().solve_power(effect_size=es, alpha=0.05, power=0.80, ratio=1.0)
```

## Time-to-event (survival) — Schoenfeld

Survival power is driven by the **number of events**, not the number of subjects. First find the
events needed for a target hazard ratio, then back out enrollment from the event rate and
follow-up.

```r
# Events needed (Schoenfeld), two-sided alpha, allocation 1:1:
hr <- 0.7; alpha <- 0.05; power <- 0.80; p <- 0.5
events <- (qnorm(1-alpha/2) + qnorm(power))^2 / (p*(1-p)*log(hr)^2)
ceiling(events)
# R packages: powerSurvEpi::ssizeCT, survival; gsDesign for group-sequential.
```

## Clustered / longitudinal designs — design effect

Ignoring clustering badly underpowers a study. Inflate the simple-random-sample n by the
**design effect** `DE = 1 + (m - 1) * ICC`, where m is the average cluster size and ICC the
intraclass correlation.

```r
n_srs <- 64                       # per arm from a simple calculation
m <- 20; icc <- 0.05
n_clustered <- n_srs * (1 + (m - 1) * icc)
```

For longitudinal/repeated-measures (e.g. MMRM), account for the number of repeated measures and
the within-subject correlation; tools: R `longpower`, `lme4` simulation.

## Other common cases

- **Non-inferiority / equivalence:** power against a margin, not against zero difference; the
  margin must be pre-specified and clinically justified.
- **Multiplicity:** if there are co-primary outcomes or multiple comparisons, adjust α (route the
  scheme to `method-evaluation`); this raises the required n.
- **Unequal allocation / dropout:** inflate n for the allocation ratio and for expected loss to
  follow-up: `n_enroll = n_complete / (1 - dropout)`.
- **Cluster RCT, prediction models (events-per-variable), interim analyses:** use design-specific
  tools (`gsDesign`, `pmsampsize` for prediction-model sample size).

## Reporting the calculation

State: design, primary outcome, test (one/two-sided), α, target power, the assumed effect (and why
it is the minimal important one), nuisance parameters (SD, baseline rate, ICC, dropout), the
resulting n (and events for survival), the software, and a **sensitivity table** across plausible
assumptions. If feasible n is below the requirement, say the study is underpowered for that effect
and give the n that would suffice.
