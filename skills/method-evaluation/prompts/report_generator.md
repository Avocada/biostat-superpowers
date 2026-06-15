# Report Generator Prompt

Use this prompt when drafting a final Statistical Method Evaluation Report.

## Prompt

Write a concise but complete Statistical Method Evaluation Report using the workflow:

`Specify -> Fit/Describe -> Diagnose -> Stress Test -> Compare -> Improve -> Report`

Required sections:

1. Evaluation scope
2. Method summary
3. Assumptions and required evidence
4. Diagnostic plan
5. Stress-test plan
6. Comparison plan or comparison results
7. Strengths
8. Limitations and risks
9. Recommended improvements
10. Integration handoff
11. Readiness rating
12. Open questions

Rules:

- Separate known results from planned checks.
- State when information is missing instead of inventing it.
- Identify which work belongs to `data-understanding-preprocessing` and which work belongs to `statistical-analysis`.
- Use method-aware language for estimates, predictions, uncertainty, and diagnostics.
- Avoid causal language unless the design and adjustment strategy support causal inference.
- Prefer actionable recommendations over broad textbook explanation.
- Include a readiness rating from `rubric.md`.

## Compact Output Pattern

```text
Evaluation scope
- Question:
- Goal type:
- Outcome/unit:
- Estimand or metric:

Method summary
- Method:
- Data/validation used:
- Current evidence:

Assumptions and required evidence
| Assumption | Why it matters | Evidence/diagnostic | Risk |

Diagnostic plan
| Check | Purpose | Failure signal | Owner |

Stress-test plan
| Test | Purpose | Failure signal | Owner |

Comparison
- Baseline:
- Alternatives:
- Fairness rules:
- Selection rule:

Strengths
- ...

Limitations and risks
| Issue | Severity | Impact | Mitigation |

Recommended improvements
| Action | Reason | Owner | Priority |

Integration handoff
- data-understanding-preprocessing:
- statistical-analysis:

Readiness rating
- Rating:
- Rationale:
- Blocking items:

Open questions
- ...
```
