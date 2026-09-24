"""Compare context payloads using a real tokenizer, without making model calls."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import tempfile

from .controller import Evaluation, Goal, Outcome, Result, Stage, WorkflowState, run
from .memory import MemoryExecutor, MemoryStore, build_prompt, render_records


def tokenizer(encoding_name):
    try:
        import tiktoken
    except ImportError as exc:
        raise RuntimeError("Install the optional demo dependency: pip install -r examples/memory/requirements.txt") from exc
    encoding = tiktoken.get_encoding(encoding_name)
    return lambda text: len(encoding.encode(text, disallowed_special=()))


def execute_fixture(task, state):
    return Result(Outcome.COMPLETE, "Synthetic fixture: specialist evidence accepted",
                  evaluation=Evaluation.READY if task.stage == Stage.EVALUATION else None,
                  missing_data_required=True if task.stage == Stage.PREPARATION else None)


def benchmark(repo_root, output, count, encoding_name):
    fixture = json.loads((repo_root / "examples/memory/confirmed_session.json").read_text())
    decisions = fixture["decisions"]
    fingerprint = hashlib.sha256(fixture["input_description"].encode()).hexdigest()
    required = {stage: tuple(d["key"] for d in decisions if stage.value in d["stages"])
                for stage in Stage if stage != Stage.DONE}
    messages = []
    for index, decision in enumerate(decisions, 1):
        messages += [{"id": f"discussion-{index}", "role": "assistant", "text": decision["discussion"]},
                     {"id": f"confirmation-{index}", "role": "user", "text": decision["value"]}]
    transcript = json.dumps(messages, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    output.mkdir(parents=True, exist_ok=True)
    # New disposable DB for each demo; never overwrite the user's real memory.
    with tempfile.TemporaryDirectory(prefix="biostat-memory-") as temp:
        db = Path(temp) / "memory.sqlite3"
        ids = itertools.count(1)
        with MemoryStore(db, fixture["project_id"], now=lambda: "2026-09-23T00:00:00+00:00",
                         new_id=lambda: f"fixture-memory-{next(ids):03d}") as store:
            for index, d in enumerate(decisions, 1):
                store.record(run_id=fixture["run_id"], key=d["key"], value=d["value"],
                             source=f"fixture://confirmed_session/confirmation-{index}",
                             confirmed_by="synthetic-user", goal=Goal.CAUSAL,
                             stages=tuple(Stage(stage) for stage in d["stages"]),
                             input_fingerprint=fingerprint if d.get("data_bound") else None)
        # Reopen to demonstrate reuse across runs, not an in-memory prompt cache.
        with MemoryStore(db, fixture["project_id"]) as store:
            all_records = render_records(store.inspect())
            prompt_sets, traces, checks = {}, {}, {}
            for arm in ("transcript_replay", "all_confirmed_memory", "stage_retrieval"):
                prompts, checks[arm] = [], []
                def callback(task, state, prompt):
                    # Deterministic evidence-coverage check, NOT a model-quality evaluation.
                    coverage = all(d["value"] in prompt for d in decisions if d["key"] in required[task.stage])
                    checks[arm].append(coverage)
                    if not coverage:
                        raise AssertionError(f"Missing required fixture decision for {task.stage}")
                    prompts.append(prompt)
                    return execute_fixture(task, state)
                if arm == "stage_retrieval":
                    executor = MemoryExecutor(store, repo_root, fingerprint, required, count, 10000, callback)
                else:
                    context = transcript if arm == "transcript_replay" else all_records
                    def executor(task, state):
                        return callback(task, state, build_prompt(repo_root, task, state, context))
                final, history = run(WorkflowState(Goal.CAUSAL), executor)
                prompt_sets[arm] = prompts
                traces[arm] = [event.route.stage.value for event in history]
                if final.stop_reason.value != "success_ready":
                    raise AssertionError(final)
            if len({tuple(trace) for trace in traces.values()}) != 1:
                raise AssertionError("Memory must preserve all workflow gates")
            totals = {arm: sum(count(prompt) for prompt in prompts) for arm, prompts in prompt_sets.items()}
            rows = [{"stage": stage, **{arm: count(prompts[i]) for arm, prompts in prompt_sets.items()}}
                    for i, stage in enumerate(traces["stage_retrieval"])]
            raw = totals["transcript_replay"]
            retrieved = totals["stage_retrieval"]
            # A stronger, hand-curated baseline shows that persistent storage alone
            # is not the source of savings. It could carry identical selected text.
            minimal = json.dumps([{ "key": d["key"], "value": d["value"]} for d in decisions], separators=(",", ":"))
            short_one_fact = decisions[0]["value"]
            single_memory = render_records(store.inspect()[:1])
            safety = {}
            with MemoryStore(db, "unrelated-project") as other:
                safety["other_project_records"] = len(other.inspect())
            safety["invalidated_on_data_change"] = len(store.invalidate_inputs("new-input-fingerprint"))
            blocked = MemoryExecutor(store, repo_root, "new-input-fingerprint", required, count, 10000,
                                     lambda *_: (_ for _ in ()).throw(AssertionError("stale data dispatched")))
            preparation = WorkflowState(Goal.CAUSAL, estimand_ready=True)
            blocked_final, _ = run(preparation, blocked)
            safety["stale_stop_reason"] = blocked_final.stop_reason.value
            safety["stale_model_calls"] = len(blocked.prompts)
            report = {
                "measurement": f"Exact text token counts: {encoding_name}; no API/model calls or billing measurement",
                "fixture_sha256": hashlib.sha256((repo_root / "examples/memory/confirmed_session.json").read_bytes()).hexdigest(),
                "tokenizer_package": "tiktoken", "tokenizer_version": __import__('tiktoken').__version__,
                "policy_sha256": {str(path.relative_to(repo_root)): hashlib.sha256(path.read_bytes()).hexdigest()
                                  for path in sorted((repo_root / 'skills').glob('*/SKILL.md'))},
                "totals": totals, "per_stage": rows,
                "reduction_vs_transcript_percent": round(100 * (raw - retrieved) / raw, 2),
                "reduction_vs_all_memory_percent": round(100 * (totals['all_confirmed_memory'] - retrieved) / totals['all_confirmed_memory'], 2),
                "project_context_only": {"transcript": count(transcript), "all_memory": count(all_records),
                                         "hand_curated_key_value_summary_without_provenance": count(minimal)},
                "short_context_counterexample": {"one_fact_text": count(short_one_fact), "one_fact_with_memory_provenance": count(single_memory)},
                "all_required_decisions_present": all(all(values) for values in checks.values()),
                "same_seven_workflow_stages": traces, "safety_checks": safety,
                "memory_creation_model_calls": 0,
                "setup": "Fixture provides explicit confirmed values; writes and retrieval are deterministic. No free LLM summarization assumed.",
                "limitations": ["Coverage checks are not clinical or LLM-quality validation.",
                                "Counts exclude message framing, hidden instructions, generated output, and reasoning tokens.",
                                "No dollar or latency savings measured; prompt-cache effects are excluded.",
                                "A host already sending the same compact context gets no further token saving from persistence alone."]}
            for arm, prompts in prompt_sets.items():
                for index, prompt in enumerate(prompts, 1):
                    (output / f"{arm}-{index:02d}.txt").write_text(prompt)
            (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
            lines = ["# Memory context demo results", "", report["measurement"], "",
                     "| Stage | Transcript replay | All confirmed memory | Stage retrieval |",
                     "|---|---:|---:|---:|"]
            for row in rows:
                lines.append(f"| {row['stage']} | {row['transcript_replay']:,} | {row['all_confirmed_memory']:,} | {row['stage_retrieval']:,} |")
            lines += [f"| **Total** | **{raw:,}** | **{totals['all_confirmed_memory']:,}** | **{retrieved:,}** |", "",
                      f"Stage retrieval reduces input text by **{report['reduction_vs_transcript_percent']}%** versus transcript replay and **{report['reduction_vs_all_memory_percent']}%** versus sending every stored record.", "",
                      "All required fixture decisions are present and all seven workflow gates run in every arm. These checks do not establish model-quality equivalence.", "",
                      f"Short-context counterexample: a single fact is {count(short_one_fact)} tokens; with memory provenance it is {count(single_memory)} tokens. Memory can increase tokens.", "",
                      f"Changed input invalidates {safety['invalidated_on_data_change']} bound records; the next preparation run stops with {safety['stale_stop_reason']} and zero model callbacks. Unrelated project records retrieved: {safety['other_project_records']}.", "",
                      "Setup uses structured, explicitly confirmed synthetic decisions; no LLM creates the memories. If a production system summarizes history with a model, count that setup input/output and validation work too.", "",
                      "No model was called. Token counts are exact for the selected text encoding, not provider billing or quality measurements. Prompt caching, output tokens, latency, and model routing are not measured.", "",
                      "See report.json for policy/fixture hashes, tokenizer version, and per-arm traces. Exact prompts are saved alongside this report."]
            (output / "report.md").write_text("\n".join(lines) + "\n")
            return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("outputs/memory-demo"))
    parser.add_argument("--encoding", choices=("o200k_base", "cl100k_base"), default="o200k_base")
    args = parser.parse_args()
    report = benchmark(Path(__file__).resolve().parents[1], args.output, tokenizer(args.encoding), args.encoding)
    print(json.dumps({key: report[key] for key in ("measurement", "totals", "reduction_vs_transcript_percent",
                                                  "reduction_vs_all_memory_percent", "all_required_decisions_present",
                                                  "short_context_counterexample", "safety_checks")}, indent=2))
    print(f"Full report and exact prompts: {args.output.resolve()}")


if __name__ == "__main__":
    main()
