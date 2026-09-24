import unittest
from dataclasses import replace
from pathlib import Path

from biostat_workflow.controller import (
    Evaluation, Goal, Outcome, Policy, Result, Stage, StopReason,
    WorkflowState, advance, route, run, settle,
)


def complete(task, state):
    return Result(Outcome.COMPLETE, "fixture evidence",
                  evaluation=Evaluation.READY if task.stage == Stage.EVALUATION else None,
                  missing_data_required=False if task.stage == Stage.PREPARATION else None)


def prepared(goal=Goal.CAUSAL, **changes):
    return replace(WorkflowState(goal, estimand_ready=True, data_ready=True), **changes)


class RoutingTests(unittest.TestCase):
    def test_all_goal_paths(self):
        for goal, model in ((Goal.CAUSAL, "statistical-analysis"),
                            (Goal.INFERENTIAL, "statistical-analysis"),
                            (Goal.DESCRIPTIVE, "statistical-analysis"),
                            (Goal.PREDICTIVE, "predictive-modeling"),
                            (Goal.FORECASTING, "predictive-modeling")):
            with self.subTest(goal=goal):
                final, history = run(WorkflowState(goal), complete)
                expected = ["study-design-and-power", "data-understanding-preprocessing"]
                if goal == Goal.CAUSAL:
                    expected.append("causal-inference")
                expected += [model, "method-evaluation", "reporting-and-reproducibility"]
                self.assertEqual([e.route.skill for e in history], expected)
                self.assertEqual(final.stop_reason, StopReason.SUCCESS)
                self.assertEqual(final.stage, Stage.DONE)
                for event in history:
                    self.assertTrue(event.route.skill_path(Path(__file__).resolve().parents[1]).is_file())

    def test_entry_stage_cannot_skip_prerequisites(self):
        state = WorkflowState(Goal.CAUSAL, stage=Stage.REPORTING,
                              analysis_ready=True, evaluation=Evaluation.READY, report_ready=True)
        self.assertEqual(route(state).stage, Stage.DESIGN)
        self.assertEqual(route(replace(state, estimand_ready=True)).stage, Stage.PREPARATION)
        self.assertEqual(route(replace(state, estimand_ready=True, data_ready=True)).stage,
                         Stage.IDENTIFICATION)

    def test_trusted_prepared_entry_avoids_repeating_design(self):
        final, events = run(prepared(), complete)
        self.assertEqual(events[0].route.stage, Stage.IDENTIFICATION)
        self.assertEqual(final.stop_reason, StopReason.SUCCESS)

    def test_missingness_precedes_identification_and_estimation(self):
        for goal in Goal:
            state = prepared(goal, missing_data_required=True)
            self.assertEqual(route(state).stage, Stage.MISSING_DATA)
            state = advance(state, Result(Outcome.COMPLETE, "imputation policy accepted"))
            expected = Stage.IDENTIFICATION if goal == Goal.CAUSAL else Stage.ANALYSIS
            self.assertEqual(route(state).stage, expected)

    def test_preparation_requires_missingness_assessment(self):
        state = WorkflowState(Goal.INFERENTIAL, estimand_ready=True)
        with self.assertRaises(ValueError):
            advance(state, Result(Outcome.COMPLETE, "data prepared"))

    def test_unready_reviews_never_report(self):
        state = prepared(identification_ready=True, analysis_ready=True)
        for rating in Evaluation:
            if rating in (Evaluation.PENDING, Evaluation.READY):
                continue
            with self.subTest(rating=rating):
                with self.assertRaises(ValueError):
                    advance(state, Result(Outcome.COMPLETE, "review", evaluation=rating))
                revised = advance(state, Result(Outcome.REVISE, "repair model",
                                  evaluation=rating, revision_target=Stage.ANALYSIS))
                self.assertEqual(route(revised).stage, Stage.ANALYSIS)
                self.assertEqual(revised.evaluation, rating)
                self.assertFalse(revised.report_ready)

    def test_review_and_reporting_are_required(self):
        state = prepared(identification_ready=True, analysis_ready=True)
        self.assertEqual(route(state).stage, Stage.EVALUATION)
        reviewed = advance(state, Result(Outcome.COMPLETE, "review", evaluation=Evaluation.READY))
        self.assertIsNone(reviewed.stop_reason)
        self.assertEqual(route(reviewed).stage, Stage.REPORTING)
        self.assertEqual(advance(reviewed, Result(Outcome.COMPLETE, "report")).stop_reason,
                         StopReason.SUCCESS)

    def test_design_revision_invalidates_all_downstream_work(self):
        state = prepared(identification_ready=True, analysis_ready=True,
                         missing_data_required=True, missing_data_ready=True)
        revised = advance(state, Result(Outcome.REVISE, "wrong target population",
                          evaluation=Evaluation.NOT_READY, revision_target=Stage.DESIGN))
        for field in ("estimand_ready", "data_ready", "identification_ready",
                      "missing_data_ready", "analysis_ready", "report_ready"):
            self.assertFalse(getattr(revised, field), field)
        self.assertEqual(revised.revision_count, 1)
        self.assertTrue(state.estimand_ready)  # Input is immutable.
        final, events = run(revised, complete)
        self.assertEqual(events[0].route.stage, Stage.DESIGN)
        self.assertEqual(final.stop_reason, StopReason.SUCCESS)

    def test_each_revision_owner_reenters_at_correct_gate(self):
        state = prepared(identification_ready=True, analysis_ready=True,
                         missing_data_required=True, missing_data_ready=True)
        for target in (Stage.PREPARATION, Stage.MISSING_DATA, Stage.IDENTIFICATION, Stage.ANALYSIS):
            with self.subTest(target=target):
                revised = advance(state, Result(Outcome.REVISE, "repair evidence",
                                  evaluation=Evaluation.NEEDS_REVISION, revision_target=target))
                self.assertEqual(route(revised).stage, target)
                self.assertFalse(revised.analysis_ready)
                self.assertNotEqual(revised.evaluation, Evaluation.READY)
                self.assertFalse(revised.report_ready)

    def test_late_missingness_from_reporting_invalidates_review(self):
        state = prepared(identification_ready=True, analysis_ready=True, evaluation=Evaluation.READY)
        revised = advance(state, Result(Outcome.REVISE, "missing confounder found",
                          revision_target=Stage.MISSING_DATA))
        self.assertEqual(route(revised).stage, Stage.MISSING_DATA)
        self.assertEqual(revised.evaluation, Evaluation.PENDING)
        self.assertFalse(revised.identification_ready)

    def test_invalid_handoffs_rejected(self):
        cases = [
            (WorkflowState(Goal.CAUSAL), Result(Outcome.REVISE, "skip", revision_target=Stage.ANALYSIS)),
            (prepared(Goal.PREDICTIVE, analysis_ready=True), Result(Outcome.REVISE, "wrong owner",
              evaluation=Evaluation.NOT_READY, revision_target=Stage.IDENTIFICATION)),
            (prepared(), Result(Outcome.COMPLETE, "wrong review owner", evaluation=Evaluation.READY)),
            (prepared(), Result(Outcome.COMPLETE, "wrong missingness owner", missing_data_required=False)),
            (prepared(), Result(Outcome.COMPLETE, "unexpected target", revision_target=Stage.DESIGN)),
            (prepared(analysis_ready=True, identification_ready=True), Result(Outcome.REVISE, "no rating",
              revision_target=Stage.ANALYSIS)),
            (prepared(), Result(Outcome.REVISE, "no target")),
        ]
        for state, result in cases:
            with self.subTest(result=result):
                with self.assertRaises(ValueError):
                    advance(state, result)


class StopTests(unittest.TestCase):
    def test_fatal_stops_immediately_from_every_reachable_stage(self):
        _, path = run(WorkflowState(Goal.CAUSAL), complete)
        for event in path:
            with self.subTest(stage=event.before.stage):
                final, history = run(event.before, lambda *_: Result(Outcome.FATAL, "fatal flaw"))
                self.assertEqual(len(history), 1)
                self.assertEqual(final.stop_reason, StopReason.HUMAN_ESCALATION)
                self.assertEqual(final.fatal_flaw, "fatal flaw")
                self.assertIsNone(route(final))

    def test_no_progress_exact_threshold(self):
        final, events = run(WorkflowState(Goal.CAUSAL),
                            lambda *_: Result(Outcome.BLOCKED, "same missing evidence"),
                            Policy(no_progress_limit=2))
        self.assertEqual(len(events), 2)
        self.assertEqual(final.no_progress_count, 2)
        self.assertEqual(final.stop_reason, StopReason.NO_PROGRESS)

    def test_completing_gate_resets_no_progress(self):
        state = WorkflowState(Goal.CAUSAL, no_progress_count=2)
        after = advance(state, Result(Outcome.COMPLETE, "target supplied"))
        self.assertEqual(after.no_progress_count, 0)

    def test_repeated_revision_without_completion_is_no_progress(self):
        final, events = run(WorkflowState(Goal.CAUSAL),
                            lambda *_: Result(Outcome.REVISE, "same unresolved estimand",
                                              revision_target=Stage.DESIGN),
                            Policy(max_revisions=10, no_progress_limit=2))
        self.assertEqual(final.stop_reason, StopReason.NO_PROGRESS)
        self.assertEqual(len(events), 2)

    def test_revision_cap_bounds_oscillation_despite_gate_progress(self):
        def reject_review(task, state):
            if task.stage == Stage.EVALUATION:
                return Result(Outcome.REVISE, "diagnostic failure", evaluation=Evaluation.NOT_READY,
                              revision_target=Stage.ANALYSIS)
            return complete(task, state)
        for limit in (0, 1, 3):
            with self.subTest(limit=limit):
                final, history = run(WorkflowState(Goal.INFERENTIAL), reject_review,
                                     Policy(max_revisions=limit, max_iterations=100))
                self.assertEqual(final.stop_reason, StopReason.MAX_REVISIONS)
                self.assertEqual(final.revision_count, limit + 1)
                self.assertEqual(sum(e.route.stage == Stage.ANALYSIS for e in history), limit + 1)
                self.assertFalse(any(e.route.stage == Stage.REPORTING for e in history))

    def test_iteration_cap_exact_boundary(self):
        final, history = run(WorkflowState(Goal.CAUSAL), complete, Policy(max_iterations=2))
        self.assertEqual(len(history), 2)
        self.assertEqual(final.stop_reason, StopReason.MAX_ITERATIONS)

    def test_success_on_last_allowed_call_wins_over_iteration_cap(self):
        final, _ = run(WorkflowState(Goal.CAUSAL), complete, Policy(max_iterations=6))
        self.assertEqual(final.stop_reason, StopReason.SUCCESS)

    def test_budget_checked_before_each_call(self):
        for allowance in (0, 2):
            with self.subTest(allowance=allowance):
                final, history = run(WorkflowState(Goal.CAUSAL), complete,
                                     budget=lambda state: state.iteration_count < allowance)
                self.assertEqual(len(history), allowance)
                self.assertEqual(final.stop_reason, StopReason.BUDGET)
                self.assertNotEqual(final.evaluation, Evaluation.READY)

    def test_terminal_state_does_not_dispatch_or_consult_budget(self):
        final, _ = run(WorkflowState(Goal.CAUSAL), complete)
        def unexpected(*_):
            self.fail("terminal state must not invoke callbacks")
        same, history = run(final, unexpected, budget=unexpected)
        self.assertEqual(same, final)
        self.assertEqual(history, ())
        with self.assertRaises(ValueError):
            advance(final, Result(Outcome.COMPLETE, "late result"))

    def test_fatal_priority_over_success_and_budget(self):
        state = prepared(identification_ready=True, analysis_ready=True,
                         evaluation=Evaluation.READY, report_ready=True, fatal_flaw="fatal")
        self.assertEqual(settle(state, budget=lambda _: False).stop_reason,
                         StopReason.HUMAN_ESCALATION)

    def test_adapter_exception_is_not_claimed_as_success(self):
        def fail(*_):
            raise RuntimeError("adapter failed")
        with self.assertRaisesRegex(RuntimeError, "adapter failed"):
            run(WorkflowState(Goal.CAUSAL), fail)

    def test_validation(self):
        for build in (lambda: WorkflowState("causal"), lambda: WorkflowState(Goal.CAUSAL, data_ready="yes"),
                      lambda: WorkflowState(Goal.CAUSAL, iteration_count=-1),
                      lambda: Policy(max_iterations=0), lambda: Policy(no_progress_limit=0),
                      lambda: Policy(max_revisions=-1), lambda: Result(Outcome.COMPLETE, ""),
                      lambda: Result("complete", "evidence")):
            with self.subTest(build=build):
                with self.assertRaises((TypeError, ValueError)):
                    build()


if __name__ == "__main__":
    unittest.main()
