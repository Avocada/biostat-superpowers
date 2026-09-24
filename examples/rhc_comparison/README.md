# RHC: original versus instrumented reproduction

The original right-heart-catheterization analysis was rerun against the same frozen public dataset, then rerun with the same estimator accompanied by controller state, persistent memory, actual MCP literature retrieval, and expanded diagnostics. The original script is preserved unchanged at `examples/demo/rhc_causal.py`.

**This is an analyst-directed reproduction and workflow audit, not two autonomous LLM runs.** Statistical point estimates should agree by design. Memory and MCP results do not dynamically choose the estimator. Jev is not installed or used. There is no measured token/cost saving or runtime speedup.

Read [RESULTS.md](RESULTS.md) for the comparison and [REVIEW.md](REVIEW.md) for the independent review. The numerical summary is in [summary.json](summary.json), with a [diagnostic figure](diagnostics.png).

## Reproduce

From the repository root, using Python 3.11 (the tested version):

```sh
python3 -m venv .venv-rhc
.venv-rhc/bin/python -m pip install -r examples/rhc_comparison/requirements.lock.txt
.venv-rhc/bin/python -m pip install -e .
mkdir -p outputs/rhc-input
curl --fail --location https://hbiostat.org/data/repo/rhc.csv -o outputs/rhc-input/rhc.csv
.venv-rhc/bin/python examples/rhc_comparison/run_comparison.py --data outputs/rhc-input/rhc.csv --output outputs/rhc-comparison-new --bootstrap 500
```

Choose a fresh output directory; the runner refuses to overwrite an existing run. Network access is required for actual PubMed MCP retrieval. The runner records the input hash; compare it with `summary.json` before claiming exact reproduction. The original data archive can change. Requirements capture the analysis environment; they are optional for ordinary skill/runtime use. Keep `.venv-rhc` outside Git.

Outputs include both original-script logs, estimates, input profile, source artifact manifests, workflow checkpoint, local SQLite memory, memory-retrieval checks, per-covariate balance, bootstrap draws/status, and diagnostics. The source data are fetched by the host, since the current MCP dataset catalog does not include RHC. The MCP tools retrieve the original study and E-value methodology from PubMed and build a reference list. Scientific diagnostic plots are rendered locally by Matplotlib.

The paired runner's estimator and diagnostics use all 5,735 patients. The causal workflow remains **blocked at missing-data review**, with identification/analysis/evaluation/report readiness unset. The blocked checkpoint is not a terminal stop. Both numerical runs are explicitly separate exploratory reproductions, not approvals that bypass the gate.

## What would require further work

An improved causal analysis needs a justified missing-data model, timing/causal-role review of day-1 covariates, a reviewed adjustment set, and sensitivity analyses appropriate to those assumptions. An autonomous-agent comparison additionally needs matched fresh model sessions, fixed prompts and budgets, actual usage telemetry, and separate runs with/without memory reuse. None of those outcomes can be inferred from the paired script reproduction.
