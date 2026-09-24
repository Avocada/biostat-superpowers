# Memory context demo results

Exact text token counts: o200k_base; no API/model calls or billing measurement

| Stage | Transcript replay | All confirmed memory | Stage retrieval |
|---|---:|---:|---:|
| design | 5,054 | 4,479 | 3,692 |
| preparation | 5,576 | 5,001 | 4,471 |
| missing_data | 4,968 | 4,393 | 3,682 |
| identification | 5,036 | 4,461 | 3,986 |
| analysis | 5,179 | 4,604 | 4,511 |
| evaluation | 5,372 | 4,797 | 4,797 |
| reporting | 4,930 | 4,355 | 4,097 |
| **Total** | **36,115** | **32,090** | **29,236** |

Stage retrieval reduces input text by **19.05%** versus transcript replay and **8.89%** versus sending every stored record.

All required fixture decisions are present and all seven workflow gates run in every arm. These checks do not establish model-quality equivalence.

Short-context counterexample: a single fact is 21 tokens; with memory provenance it is 93 tokens. Memory can increase tokens.

Changed input invalidates 4 bound records; the next preparation run stops with no_progress_threshold and zero model callbacks. Unrelated project records retrieved: 0.

Setup uses structured, explicitly confirmed synthetic decisions; no LLM creates the memories. If a production system summarizes history with a model, count that setup input/output and validation work too.

No model was called. Token counts are exact for the selected text encoding, not provider billing or quality measurements. Prompt caching, output tokens, latency, and model routing are not measured.

See [results.json](results.json) for policy/fixture hashes, tokenizer version, and per-arm traces. Re-run `python -m biostat_workflow.memory_demo` with the optional tokenizer installed to regenerate exact prompts under `outputs/memory-demo/`. See [the memory architecture](../../docs/modernization/MEMORY.md) for setup, limitations, and integration.
