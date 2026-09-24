"""Synthetic causal control-flow demonstration, not a fitted clinical analysis."""
import argparse
from pathlib import Path
from .controller import (Evaluation, Goal, Outcome, Policy, Result, Stage,
                         WorkflowState, run)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=("success", "revision", "fatal", "stalled"), default="revision")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]

    def execute(task, state):
        task.skill_path(root)  # A real host reads and executes this domain policy.
        if args.scenario == "stalled":
            return Result(Outcome.BLOCKED, "Synthetic fixture: target population remains unspecified")
        if task.stage == Stage.IDENTIFICATION and args.scenario == "fatal":
            return Result(Outcome.FATAL, "Synthetic fixture: treatment has no overlap; human review required")
        if task.stage == Stage.EVALUATION:
            if args.scenario == "revision" and state.revision_count == 0:
                return Result(Outcome.REVISE, "Synthetic fixture: time-zero audit needs repair",
                              evaluation=Evaluation.NOT_READY, revision_target=Stage.PREPARATION)
            return Result(Outcome.COMPLETE, "Synthetic fixture: review passed", evaluation=Evaluation.READY)
        if task.stage == Stage.PREPARATION:
            return Result(Outcome.COMPLETE, "Synthetic fixture: cohort contract; missing confounder plan needed",
                          missing_data_required=True)
        return Result(Outcome.COMPLETE, "Synthetic fixture: required evidence accepted")

    print("CONTROL-FLOW FIXTURE ONLY: treatment A vs B, 30-day risk difference in an observational cohort")
    final, history = run(WorkflowState(Goal.CAUSAL), execute, Policy())
    for event in history:
        print(f"{event.after.iteration_count:02d} {event.route.stage.value} [{event.route.skill}]"
              f" -> {event.after.stage.value}: {event.result.outcome.value}; {event.route.reason}"
              f"; revisions={event.after.revision_count}; no_progress={event.after.no_progress_count}")
        print(f"   {event.result.evidence}")
    print(f"STOP: {final.stop_reason.value}")


if __name__ == "__main__":
    main()
