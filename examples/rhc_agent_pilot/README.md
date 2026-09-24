# RHC fresh-agent pilot: quality, tools and memory

[Open the offline visual comparison](index.html). Both full reports and both fresh-session follow-ups are included. This extends the earlier `rhc_comparison` deterministic script audit: these are new autonomous agent runs, not the same script with instrumentation.

## Outcome

The upgraded workflow demonstrated actual MCP use, persistent decision retrieval and explicit blocked lifecycle states. It did **not** demonstrate token savings or clearly superior visualization in this pilot.

| Measured dimension | Original skills | Controller + memory + MCP |
|---|---:|---:|
| Independent initial artifact score | 81.7/100 | 83.3/100 |
| Main statistical figures, initial | 5 | 5, plus MCP age histogram |
| Initial uncached input tokens | 57,809 | 73,440 |
| Follow-up uncached input tokens | 41,402 | 73,721 |
| Both phases: uncached input tokens | 99,211 | 147,161 |
| Both phases: total input tokens | 1,093,259 | 1,465,177 |
| Both phases: output tokens | 20,688 | 26,753 |
| Initial elapsed minutes | 7.97 | 9.85 |
| Follow-up elapsed minutes | 3.82 | 5.40 |

The upgraded arm used **48.3% more uncached input** and **29.3% more output** across both phases; follow-up uncached input was **78.1% higher**. Total input includes cached tokens; it is not the context-window size or a billed dollar total. Reasoning output is reported separately by the host and is not added a second time to output. Setup, parent orchestration, independent review and failed CLI startup attempts are outside these four turn totals. This is analysis-session usage, not all project-development usage.

The score difference is subjective and small, not proof of superior performance. Read [the independent review](independent_review.md), which inspected all analytical PNGs and checked results. The parent additionally rendered the initial reports, follow-ups and comparison page in Chrome and checked images/layout. The original arm artifacts are preserved without retrospective scientific fixes.

## What improved, and what did not

- **Science:** both recovered the same crude and legacy-weighted point estimates and declined causal identification. Baseline detected 11 no-death labels with last contact before day 30. Upgraded added missingness-indicator balance: ADL missingness remained imbalanced despite balance on encoded propensity inputs. Neither bootstrap implementation is ready for definitive inference (80 versus 120 replicates, incomplete warning/success policies).
- **Visuals:** both produced readable, offline interactive reports with cohort, missingness, diagnostics, effects and sensitivity graphics. Five main figures in each used Matplotlib. Upgraded additionally used the MCP renderer for an age histogram. It would be misleading to attribute all its visualization to MCP or declare an aesthetic winner from this one pair.
- **MCP:** five actual initial calls imported the staged CSV, searched PubMed, listed chart examples, profiled the data and rendered a histogram. Follow-up reused existing source artifacts rather than refetching them. See `mcp_calls.json`. Local staging is explicit host input, not an automatic RHC database connector; host-supplied source attribution is marked unverified.
- **Memory:** four attributed, scoped decisions persisted and were retrieved in a fresh session, then a new dependent sensitivity record was appended. First lookup used a CSV hash where the stored scope required a composite data/dictionary/script/contract fingerprint; that lookup correctly returned no usable records. Reconstructing the matching fingerprint recovered all four records (2,070 UTF-8 bytes). These bytes are **not** model tokens or demonstrated savings. Baseline also successfully reused ordinary notes and pure analysis functions. Both avoided rerunning the initial bootstrap and full discovery.
- **Control:** upgraded recorded blocked causal preparation and blocked independent-review gates. It did not fabricate causal success or human approval. This runtime records host-supplied evidence; it is not an autonomous statistical analyst and the reports' choices remain partly hard-coded.

The overhead includes learning/reading runtime APIs and extra audit steps; the fingerprint mismatch added work. One bundled comparison cannot estimate how much each contributes. Structured memory is useful for traceability and guarded reuse here, but an efficiency claim needs a lighter integration and repeated tests against a baseline that can also save good notes.

## Matched follow-up result

Both arms removed only `adld3p` and `urin1`, retained all 5,735 patients and `cat2`, and compared clipping at .01/.02/.05. At .02 the exploratory RD changed from 5.00 to 5.51 percentage points and RR from 1.158 to 1.175. Dropping these potential confounders worsened ADL balance. No new intervals were claimed; deleting variables is a sensitivity exercise, not a repair establishing causality.

## Design and reproducibility

- Model `gpt-6-astra`, medium effort, fresh ephemeral session per phase/arm; CLI 0.155.0-alpha.16. Same supplied data, shared scientific environment and common request. Each phase had a 600-second wall cap. Both completed within the cap. No model delegation inside an arm.
- Original nine skills versus those skills plus development runtime at parent commit `37367058012a8adf47a830eb86f35e1aac556643` and the local CSV/bar-chart changes published with this pilot. Jev excluded. The study-specific MCP server was confined to its staged input folder; no global unrestricted import directory was enabled.
- `protocol.json` and prompts preserve the task and evaluation criteria. `launch.py` preserves the actual local launch configuration and requires adapting its absolute paths to rerun elsewhere. `collect.py` extracts telemetry and checks preservation; `build_comparison.py` builds the offline overview. Authentication and a compatible model/CLI are prerequisites for new agent runs; those runs incur usage.
- Data: https://hbiostat.org/data/repo/rhc.csv ; dictionary https://hbiostat.org/data/repo/rhc.html ; original PMID 8782638. Original CSV SHA256 `9ef4ab578be4b40ad5d97d3a7e08ffdc1f9f76aeeefee51b4996e4221556f8e8`. Remove only the unnamed archive index column; normalized analysis SHA256 `811bad3c113c26acc64c00ed149993b09dd320cf2540b750738f5656233d2ec6`. Both snapshots had identical input bytes. Input snapshots and raw event logs remain local under ignored outputs; participant rows are not included in this published example.
- Each arm includes its analysis/report scripts, aggregate results/tables, environment versions and saved decisions. To reproduce calculations, supply the matching input files under that arm's `input/` and adapt the documented Python/runtime paths. Upgraded initial analysis also requires its recorded MCP artifact snapshot; this aggregate publication is not a replacement for that local provenance store. A new end-to-end run must obtain fresh MCP artifacts and corresponding IDs; do not fabricate old provenance.
- Initial broad font discovery stalled in both runs; each agent recovered using existing font metadata. Other recoverable command errors and unequal chosen bootstrap counts remain in the measured turns. We did not rerun selectively to improve the result.
- `initial_preservation.json` verifies the initial reports, results and figures remained byte-for-byte unchanged after follow-up. Raw transcripts and participant-level MCP snapshots are deliberately excluded from publication. Local archival paths are historical provenance, not portable links.

## Next development priorities

1. Provide a small, documented resume helper that reconstructs/verifies the composite fingerprint and returns relevant decisions plus artifact pointers in one call, without rereading the full memory implementation.
2. Connect decisions to executable configuration and validation, rather than keyword assertions and prose alone; test stale/conflicting records without weakening gates.
3. Add scientific chart contracts/templates (balance, overlap, effect intervals, missingness) and visual regression checks. Generic galleries do not replace statistical diagnostics.
4. Combine the complementary audits: follow-up completeness, missingness balance, convergence/finite-result checks and explicit bootstrap success criteria.
5. Repeat a preregistered, multi-case comparison with a memory-only ablation before claiming token efficiency. Keep Jev deferred.
