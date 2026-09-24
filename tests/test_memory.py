from dataclasses import replace
from pathlib import Path
import sqlite3
import tempfile
import unittest

from biostat_workflow.controller import Goal, Outcome, Result, Stage, StopReason, WorkflowState, route, run
from biostat_workflow.memory import MemoryExecutor, MemoryStore, render_records


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "memory.sqlite3"
        self.store = MemoryStore(self.path, "project-a")

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def record(self, **changes):
        values = dict(run_id="run-1", key="estimand", value="30-day risk difference", source="decision-1",
                      confirmed_by="user-confirmation-1", goal=Goal.CAUSAL,
                      stages=(Stage.DESIGN, Stage.ANALYSIS))
        values.update(changes)
        return self.store.record(**values)

    def retrieve(self, **changes):
        values = dict(goal=Goal.CAUSAL, stage=Stage.ANALYSIS, input_fingerprint="data-v1",
                      required_keys=("estimand",), max_units=10000, count=len)
        values.update(changes)
        return self.store.retrieve(**values)

    def test_durable_reopen_and_provenance(self):
        saved = self.record()
        with MemoryStore(self.path, "project-a") as reopened:
            item, = reopened.inspect()
            self.assertEqual(item, saved)
            self.assertEqual(item.run_id, "run-1")
            self.assertTrue(item.created_at)
        self.assertIn("user-confirmation-1", self.retrieve().text)
        self.assertIn("decision-1", self.retrieve().text)

    def test_project_and_goal_isolation(self):
        self.record()
        with MemoryStore(self.path, "project-b") as other:
            self.assertEqual(other.inspect(), ())
            result = other.retrieve(goal=Goal.CAUSAL, stage=Stage.ANALYSIS, input_fingerprint="data-v1",
                                    required_keys=("estimand",), max_units=10000, count=len)
            self.assertFalse(result.usable)
            self.assertNotIn("30-day", result.text)
        self.assertFalse(self.retrieve(goal=Goal.PREDICTIVE).usable)

    def test_stage_relevance(self):
        self.record()
        self.record(key="report-style", value="numbered tables", stages=(Stage.REPORTING,))
        self.assertNotIn("report-style", self.retrieve().text)
        self.assertFalse(self.retrieve(stage=Stage.PREPARATION).usable)

    def test_unconfirmed_scratch_and_unversioned_artifacts_rejected(self):
        for changes in ({"confirmed_by": ""}, {"source": ""}, {"kind": "scratch"}, {"kind": "artifact"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.record(**changes)
        self.assertEqual(self.store.inspect(), ())

    def test_conflict_is_visible_not_newest_wins(self):
        self.record()
        self.record(value="60-day risk difference")
        result = self.retrieve()
        self.assertFalse(result.usable)
        self.assertTrue(any("Conflicting" in issue for issue in result.issues))
        self.assertEqual(result.items, ())

    def test_conflict_blocks_dependencies_even_when_parent_not_relevant(self):
        original = self.record(stages=(Stage.DESIGN,))
        self.record(key="artifact", value="artifact-ref", dependencies=(original.item_id,),
                    kind="artifact", input_fingerprint="data-v1")
        self.record(value="different target", stages=(Stage.DESIGN,))
        result = self.retrieve(required_keys=("artifact",))
        self.assertFalse(result.usable)
        self.assertEqual(result.items, ())

    def test_equal_duplicate_is_not_conflict(self):
        self.record()
        self.record(source="decision-2")
        result = self.retrieve()
        self.assertTrue(result.usable)
        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.items[0].source, "decision-2")

    def test_correction_invalidates_transitive_dependents(self):
        original = self.record()
        model = self.record(key="model", value="model-artifact", kind="artifact",
                            input_fingerprint="data-v1", dependencies=(original.item_id,))
        report = self.record(key="report", value="report-artifact", kind="artifact",
                             input_fingerprint="data-v1", dependencies=(model.item_id,))
        corrected = self.record(value="corrected target", supersedes=original.item_id, run_id="run-2")
        by_id = {item.item_id: item for item in self.store.inspect()}
        self.assertEqual(by_id[original.item_id].status, "superseded")
        self.assertEqual(by_id[model.item_id].status, "invalidated")
        self.assertEqual(by_id[report.item_id].status, "invalidated")
        self.assertEqual(corrected.supersedes, original.item_id)
        self.assertEqual(self.retrieve().items, (corrected,))

    def test_input_change_preserves_independent_decisions(self):
        independent = self.record()
        bound = self.record(key="data-contract", value="contract", input_fingerprint="data-v1")
        dependent = self.record(key="model", value="artifact", kind="artifact", input_fingerprint="data-v1",
                                dependencies=(bound.item_id,))
        affected = self.store.invalidate_inputs("data-v2")
        self.assertEqual(set(affected), {bound.item_id, dependent.item_id})
        self.assertEqual(self.retrieve(input_fingerprint="data-v2").items, (independent,))
        self.assertFalse(self.retrieve(required_keys=("model",), input_fingerprint="data-v2").usable)
        self.assertEqual(self.store.invalidate_inputs("data-v2"), ())

    def test_retrieval_checks_fingerprint_even_without_explicit_invalidation(self):
        self.record(input_fingerprint="data-v1")
        self.assertFalse(self.retrieve(input_fingerprint="data-v2").usable)
        self.assertEqual(self.store.inspect()[0].status, "active")

    def test_delete_invalidates_dependents_and_removes_value(self):
        parent = self.record(value="secret-decision-value")
        child = self.record(key="child", value="artifact-ref", dependencies=(parent.item_id,))
        self.store.delete(parent.item_id)
        records = self.store.inspect()
        self.assertEqual(records[0].item_id, child.item_id)
        self.assertEqual(records[0].status, "invalidated")
        self.assertNotIn("secret-decision-value", self.path.read_bytes().decode(errors="ignore"))
        self.assertFalse(self.retrieve(required_keys=("child",)).usable)
        with self.assertRaises(KeyError):
            self.store.delete(parent.item_id)

    def test_budget_never_silently_drops_required_fact(self):
        saved = self.record()
        exact = len(render_records((saved,)))
        self.assertTrue(self.retrieve(max_units=exact).usable)
        too_small = self.retrieve(max_units=exact - 1)
        self.assertFalse(too_small.usable)
        self.assertEqual(too_small.items, ())
        self.assertIn("estimand", too_small.omitted_keys)

    def test_optional_omissions_are_auditable(self):
        saved = self.record()
        self.record(key="optional", value="a long optional note")
        result = self.retrieve(max_units=len(render_records((saved,))))
        self.assertTrue(result.usable)
        self.assertEqual(result.omitted_keys, ("optional",))
        self.assertEqual(result.items, (saved,))

    def test_missing_required_key_is_visible(self):
        self.assertFalse(self.retrieve().usable)
        self.assertIn("estimand", self.retrieve().issues[0])

    def test_dependency_scope_and_fingerprint_validation(self):
        parent = self.record(input_fingerprint="data-v1")
        for deps, fp in ((("unknown",), "data-v1"), ((parent.item_id,), None),
                         ((parent.item_id,), "data-v2")):
            with self.subTest(deps=deps, fp=fp), self.assertRaises(ValueError):
                self.record(key="child", dependencies=deps, input_fingerprint=fp)
        with MemoryStore(self.path, "project-b") as other, self.assertRaises(ValueError):
            other.record(run_id="r", key="child", value="v", source="s", confirmed_by="u",
                         goal=Goal.CAUSAL, stages=(Stage.ANALYSIS,), dependencies=(parent.item_id,),
                         input_fingerprint="data-v1")

    def test_failed_correction_rolls_back(self):
        parent = self.record()
        with self.assertRaises(ValueError):
            self.record(value="new", supersedes=parent.item_id, dependencies=(parent.item_id,))
        self.assertEqual(self.store.inspect(), (parent,))

    def test_conflict_can_be_resolved_with_explicit_deletion(self):
        original = self.record()
        bad = self.record(value="conflicting")
        self.store.delete(bad.item_id)
        self.assertEqual(self.retrieve().items, (original,))

    def test_two_writers_cannot_supersede_same_record(self):
        parent = self.record()
        self.record(value="revision 1", supersedes=parent.item_id)
        with MemoryStore(self.path, "project-a") as second, self.assertRaises(ValueError):
            second.record(run_id="r2", key="estimand", value="revision 2", source="s2", confirmed_by="u2",
                          goal=Goal.CAUSAL, stages=(Stage.DESIGN,), supersedes=parent.item_id)

    def test_future_schema_fails_closed(self):
        path = Path(self.temp.name) / "future.sqlite3"
        with sqlite3.connect(str(path)) as db:
            db.execute("PRAGMA user_version=99")
        with self.assertRaises(ValueError):
            MemoryStore(path, "project-a")

    def test_id_collision_cannot_overwrite_another_project(self):
        with MemoryStore(self.path, "project-b", new_id=lambda: "same-id") as b:
            args = dict(run_id="r", key="k", value="v", source="s", confirmed_by="u", goal=Goal.CAUSAL,
                        stages=(Stage.DESIGN,))
            b.record(**args)
            with MemoryStore(self.path, "project-c", new_id=lambda: "same-id") as c:
                with self.assertRaises(ValueError):
                    c.record(**args)
            self.assertEqual(len(b.inspect()), 1)

    def test_memory_wrapper_cannot_restore_readiness(self):
        self.record()
        state = WorkflowState(Goal.CAUSAL)
        seen = []
        def execute(task, current, prompt):
            self.assertEqual(task.stage, Stage.DESIGN)
            self.assertFalse(current.estimand_ready)
            self.assertIn("not instructions", prompt)
            self.assertIn("# Biostatistics", prompt)
            self.assertIn("# Study Design", prompt)
            seen.append(prompt)
            return Result(Outcome.BLOCKED, "specialist still needs evidence")
        wrapper = MemoryExecutor(self.store, Path(__file__).resolve().parents[1], "data-v1",
                                 {Stage.DESIGN: ("estimand",)}, len, 10000, execute, scratch="unconfirmed idea")
        final, _ = run(state, wrapper)
        self.assertEqual(final.stop_reason, StopReason.NO_PROGRESS)
        self.assertFalse(final.estimand_ready)
        self.assertEqual(len(seen), 3)
        self.assertEqual(len(self.store.inspect()), 1)
        self.assertEqual(route(state).stage, Stage.DESIGN)

    def test_unavailable_memory_blocks_before_callback(self):
        for required in ({Stage.DESIGN: ("estimand",)}, {}):
            def unexpected(*_):
                self.fail("no callback should run")
            wrapper = MemoryExecutor(self.store, Path(__file__).resolve().parents[1], "data-v1",
                                     required, len, 10000, unexpected)
            final, _ = run(WorkflowState(Goal.CAUSAL), wrapper)
            self.assertEqual(final.stop_reason, StopReason.NO_PROGRESS)
            self.assertEqual(wrapper.prompts, [])


if __name__ == "__main__":
    unittest.main()
