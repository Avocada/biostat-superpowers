"""Deterministic, synchronous workflow routing with bounded specialist calls.

The host executes the returned skill and supplies a Result. No model, network,
statistical implementation, or installed-skill mutation is performed here.
"""
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path
from typing import Callable, Optional


class Goal(str, Enum):
    DESCRIPTIVE = "descriptive"
    INFERENTIAL = "inferential"
    CAUSAL = "causal"
    PREDICTIVE = "predictive"
    FORECASTING = "forecasting"


class Stage(str, Enum):
    DESIGN = "design"
    PREPARATION = "preparation"
    MISSING_DATA = "missing_data"
    IDENTIFICATION = "identification"
    ANALYSIS = "analysis"
    EVALUATION = "evaluation"
    REPORTING = "reporting"
    DONE = "done"


class Evaluation(str, Enum):
    PENDING = "pending"
    READY = "ready"
    CONDITIONALLY_READY = "conditionally_ready"
    NEEDS_REVISION = "needs_revision"
    NOT_READY = "not_ready"
    INSUFFICIENT_INFORMATION = "insufficient_information"


class StopReason(str, Enum):
    SUCCESS = "success_ready"
    HUMAN_ESCALATION = "fatal_flaw_human_escalation"
    NO_PROGRESS = "no_progress_threshold"
    MAX_REVISIONS = "max_revisions"
    MAX_ITERATIONS = "max_iterations"
    BUDGET = "budget_exhausted"


class Outcome(str, Enum):
    COMPLETE = "complete"
    BLOCKED = "blocked"
    REVISE = "revise"
    FATAL = "fatal"


@dataclass(frozen=True)
class WorkflowState:
    goal: Goal
    stage: Stage = Stage.DESIGN
    estimand_ready: bool = False
    data_ready: bool = False
    identification_ready: bool = False
    missing_data_required: bool = False
    missing_data_ready: bool = False
    analysis_ready: bool = False
    evaluation: Evaluation = Evaluation.PENDING
    report_ready: bool = False
    revision_count: int = 0
    no_progress_count: int = 0
    iteration_count: int = 0
    stop_reason: Optional[StopReason] = None
    fatal_flaw: Optional[str] = None

    def __post_init__(self):
        for value, kind in ((self.goal, Goal), (self.stage, Stage),
                            (self.evaluation, Evaluation)):
            if not isinstance(value, kind):
                raise TypeError(f"Expected {kind.__name__}, got {value!r}")
        if self.stop_reason is not None and not isinstance(self.stop_reason, StopReason):
            raise TypeError("stop_reason must be a StopReason")
        for name in ("revision_count", "no_progress_count", "iteration_count"):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise ValueError(f"{name} must be a nonnegative integer")
        for name in ("estimand_ready", "data_ready", "identification_ready",
                     "missing_data_required", "missing_data_ready", "analysis_ready", "report_ready"):
            if type(getattr(self, name)) is not bool:
                raise TypeError(f"{name} must be a bool")


@dataclass(frozen=True)
class Policy:
    max_revisions: int = 3
    max_iterations: int = 30
    no_progress_limit: int = 3

    def __post_init__(self):
        for name in ("max_revisions", "max_iterations", "no_progress_limit"):
            value = getattr(self, name)
            minimum = 0 if name == "max_revisions" else 1
            if type(value) is not int or value < minimum:
                raise ValueError(f"{name} must be an integer >= {minimum}")


@dataclass(frozen=True)
class Route:
    stage: Stage
    skill: str
    reason: str

    def skill_path(self, repo_root: Path) -> Path:
        """Resolve policy in the development repo, never the installed skill tree."""
        path = repo_root / "skills" / self.skill / "SKILL.md"
        if not path.is_file():
            raise FileNotFoundError(path)
        return path


@dataclass(frozen=True)
class Result:
    outcome: Outcome
    evidence: str
    evaluation: Optional[Evaluation] = None
    revision_target: Optional[Stage] = None
    missing_data_required: Optional[bool] = None

    def __post_init__(self):
        if not isinstance(self.outcome, Outcome):
            raise TypeError("outcome must be an Outcome")
        if not isinstance(self.evidence, str) or not self.evidence.strip():
            raise ValueError("A result requires an evidence reference or explanation")
        if self.evaluation is not None and not isinstance(self.evaluation, Evaluation):
            raise TypeError("evaluation must be an Evaluation")
        if self.revision_target is not None and not isinstance(self.revision_target, Stage):
            raise TypeError("revision_target must be a Stage")
        if self.missing_data_required is not None and type(self.missing_data_required) is not bool:
            raise TypeError("missing_data_required must be a bool")


@dataclass(frozen=True)
class Transition:
    before: WorkflowState
    route: Route
    result: Result
    after: WorkflowState


SKILLS = {
    Stage.DESIGN: "study-design-and-power",
    Stage.PREPARATION: "data-understanding-preprocessing",
    Stage.MISSING_DATA: "missing-data",
    Stage.IDENTIFICATION: "causal-inference",
    Stage.ANALYSIS: "statistical-analysis",
    Stage.EVALUATION: "method-evaluation",
    Stage.REPORTING: "reporting-and-reproducibility",
}


def route(state: WorkflowState) -> Optional[Route]:
    """Readiness gates override a caller's requested lifecycle entry stage."""
    if state.stop_reason is not None or state.fatal_flaw:
        return None
    checks = (
        (not state.estimand_ready, Stage.DESIGN, "Define the estimand or prediction target"),
        (not state.data_ready, Stage.PREPARATION, "Establish the analysis-ready data contract"),
        (state.missing_data_required and not state.missing_data_ready,
         Stage.MISSING_DATA, "Resolve non-trivial missingness before estimation"),
        (state.goal == Goal.CAUSAL and not state.identification_ready,
         Stage.IDENTIFICATION, "Identify the causal contrast before estimation"),
        (not state.analysis_ready, Stage.ANALYSIS, "Execute the goal-appropriate analysis"),
        (state.evaluation != Evaluation.READY, Stage.EVALUATION, "Critique before reporting"),
        (not state.report_ready, Stage.REPORTING, "Produce the reviewed reproducible report"),
    )
    for needed, stage, reason in checks:
        if needed:
            skill = SKILLS[stage]
            if stage == Stage.ANALYSIS and state.goal in (Goal.PREDICTIVE, Goal.FORECASTING):
                skill = "predictive-modeling"
            return Route(stage, skill, reason)
    return None


# True means another specialist call is affordable. The host owns cost/time accounting.
BudgetHook = Callable[[WorkflowState], bool]
Executor = Callable[[Route, WorkflowState], Result]


def settle(state: WorkflowState, policy: Policy = Policy(),
           budget: Optional[BudgetHook] = None) -> WorkflowState:
    """Evaluate terminal conditions before dispatch; terminal states are immutable."""
    if state.stop_reason is not None:
        return state
    next_route = route(state)
    reason = None
    if state.fatal_flaw:
        reason = StopReason.HUMAN_ESCALATION
    elif next_route is None:
        reason = StopReason.SUCCESS
    elif state.revision_count > policy.max_revisions:
        reason = StopReason.MAX_REVISIONS
    elif state.no_progress_count >= policy.no_progress_limit:
        reason = StopReason.NO_PROGRESS
    elif state.iteration_count >= policy.max_iterations:
        reason = StopReason.MAX_ITERATIONS
    elif budget is not None and not budget(state):
        reason = StopReason.BUDGET
    stage = Stage.DONE if reason == StopReason.SUCCESS else (next_route.stage if next_route else state.stage)
    return replace(state, stage=stage, stop_reason=reason)


def _invalidate(state: WorkflowState, target: Stage) -> WorkflowState:
    """Invalidate the target and all dependent evidence, conservatively."""
    updates = dict(analysis_ready=False, evaluation=Evaluation.PENDING, report_ready=False)
    if target == Stage.DESIGN:
        updates["estimand_ready"] = False
    if target in (Stage.DESIGN, Stage.PREPARATION):
        updates.update(data_ready=False, missing_data_ready=False)
    if target in (Stage.DESIGN, Stage.PREPARATION, Stage.MISSING_DATA, Stage.IDENTIFICATION):
        updates["identification_ready"] = False
    if target == Stage.MISSING_DATA:
        updates.update(missing_data_required=True, missing_data_ready=False)
    return replace(state, **updates)


def advance(state: WorkflowState, result: Result, policy: Policy = Policy()) -> WorkflowState:
    """Apply one validated result to the current route, without mutating the input."""
    state = settle(state, policy)
    if state.stop_reason is not None:
        raise ValueError("Cannot advance a stopped workflow")
    current = route(state)
    assert current is not None
    if result.evaluation is not None and current.stage != Stage.EVALUATION:
        raise ValueError("Only method-evaluation can supply a readiness rating")
    if result.missing_data_required is not None and not (
        current.stage == Stage.PREPARATION and result.outcome == Outcome.COMPLETE
    ):
        raise ValueError("Missingness assessment belongs to completed preparation; use a revision for later findings")
    if result.revision_target is not None and result.outcome != Outcome.REVISE:
        raise ValueError("revision_target requires a revise outcome")
    if result.evaluation is not None and result.outcome not in (Outcome.COMPLETE, Outcome.REVISE):
        raise ValueError("Readiness ratings require complete or revise")
    updated = replace(state, iteration_count=state.iteration_count + 1)
    if result.outcome == Outcome.FATAL:
        updated = replace(updated, fatal_flaw=result.evidence)
    elif result.outcome == Outcome.BLOCKED:
        updated = replace(updated, no_progress_count=state.no_progress_count + 1)
    elif result.outcome == Outcome.REVISE:
        target = result.revision_target
        allowed = (Stage.DESIGN, Stage.PREPARATION, Stage.MISSING_DATA,
                   Stage.IDENTIFICATION, Stage.ANALYSIS)
        if target not in allowed or (target == Stage.IDENTIFICATION and state.goal != Goal.CAUSAL):
            raise ValueError("Revision requires a goal-appropriate upstream owner")
        if list(Stage).index(target) > list(Stage).index(current.stage):
            raise ValueError("A revision cannot skip forward past the current stage")
        if current.stage == Stage.EVALUATION and result.evaluation in (None, Evaluation.PENDING, Evaluation.READY):
            raise ValueError("Review revision requires a non-ready rating")
        updated = _invalidate(updated, target)
        updated = replace(updated, revision_count=state.revision_count + 1,
                          no_progress_count=state.no_progress_count + 1,
                          evaluation=result.evaluation or Evaluation.PENDING)
    else:
        if current.stage == Stage.EVALUATION:
            if result.evaluation != Evaluation.READY:
                raise ValueError("Only ready review can complete; other ratings require revision")
            updated = replace(updated, evaluation=Evaluation.READY)
        else:
            field = {Stage.DESIGN: "estimand_ready", Stage.PREPARATION: "data_ready",
                     Stage.MISSING_DATA: "missing_data_ready", Stage.IDENTIFICATION: "identification_ready",
                     Stage.ANALYSIS: "analysis_ready", Stage.REPORTING: "report_ready"}[current.stage]
            updated = replace(updated, **{field: True})
            if current.stage == Stage.PREPARATION:
                if result.missing_data_required is None:
                    raise ValueError("Preparation must explicitly assess missingness")
                updated = replace(updated, missing_data_required=result.missing_data_required)
        updated = replace(updated, no_progress_count=0)
    return settle(updated, policy)


def run(state: WorkflowState, execute: Executor, policy: Policy = Policy(),
        budget: Optional[BudgetHook] = None) -> tuple[WorkflowState, tuple[Transition, ...]]:
    """Run serial specialist callbacks until stopped. Exceptions propagate to the host.

    The hook runs before every call. Hard cancellation of an in-flight callback,
    retries, and durable checkpoints belong to a future adapter layer.
    """
    history = []
    while True:
        state = settle(state, policy, budget)
        if state.stop_reason is not None:
            return state, tuple(history)
        current = route(state)
        assert current is not None
        result = execute(current, state)
        after = advance(state, result, policy)
        history.append(Transition(state, current, result, after))
        state = after
