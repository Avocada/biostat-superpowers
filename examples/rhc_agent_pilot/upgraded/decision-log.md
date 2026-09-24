# Decision log · analyst-authored

- Defined primary target before fitting: supplied-label crude 30-day RD/RR in all supplied patients. No claim of preregistration.
- Confirmed input SHA against SOURCE.md; retained original legacy file and identical patient data.
- Read original specialist policies; no delegation per study instructions. Independent scientific review remains pending.
- Used dictionary and retrieved PMID 8782638 abstract to distinguish qualifying study day from first 24 hours of ICU care and published matching from legacy weighting.
- MCP profile showed three highly incomplete candidate fields. Retained legacy encoding only for exploratory reproduction; no silent complete-case deletion. Missing-data mechanism unconfirmed; MI/MNAR work deferred pending timing and structural-blank adjudication.
- MemoryStore recorded four analyst-reviewed scoped records with composite input/contract fingerprint, then retrieved them before analysis. Retrieval constrained model labeling, missingness diagnostics and source comparison; it did not authorize readiness.
- Executed actual controller transitions. Causal branch blocked on preparation; inferential branch blocked on independent evaluation. Stop policy is one blocked result, appropriate to this bounded audit. No reporting/causal completion or human confirmation was fabricated.
- Reproduced C=1 standardized logistic propensity, median fill, 0.02 clipping and stabilized normalized risks. Added 120 patient bootstrap refits. No interval claimed to cover confounding, timing, imputation-model uncertainty or hospital clustering.
- Used fixed unweighted pooled SD for before/after SMD; preserved all terms. Added clipping and missingness encoding/omission sensitivities without selecting a preferred causal model.
- Follow-up needs: exact treatment/measurement timestamps and time-zero definition; structural cat2 blanks; clinical sentinel/range review; defensible DAG/adjustment set; congenial MI and MNAR sensitivity; site-aware uncertainty; independent artifact review.

- Visual QA: displayed and inspected all six saved figure PNGs; moved overlapping missingness legend and re-inspected. Checked embedded HTML assets, counts, SQLite integrity and controller terminal states. HTML was not browser-render tested. Initial font discovery stalled before fitting; reused existing font metadata in project-local cache, with no global changes.
