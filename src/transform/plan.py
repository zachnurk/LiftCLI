"""Transform: run the rules on every exercise from the last session to build
today's plan."""

from src.settings import SLEEP_HOURS_BELOW_WHICH_WEIGHT_AND_REPS_HOLD
from src.transform.rules import (
    accessories_to_skip,
    add_one_rep,
    drop_after_stall,
    drop_when_reps_far_below_range,
    hold_on_short_sleep,
    step_up_after_go_up_reps,
)


def arrow_for_change(last_weight, today_weight):
    """Up arrow if the weight went up, down arrow if it went down, else blank."""
    if today_weight > last_weight:
        return "↑"
    if today_weight < last_weight:
        return "↓"
    return ""


def plan_exercise(exercise, history, sleep_hours):
    """Return (today_weight, today_aim, rule_label). Rules run top to bottom and
    the first one that returns a plan wins. add_one_rep always returns one."""
    plan = hold_on_short_sleep(exercise, history, sleep_hours)
    if plan:
        return *plan, "short sleep"

    plan = drop_when_reps_far_below_range(exercise, history, sleep_hours)
    if plan:
        return *plan, "too few reps"

    plan = drop_after_stall(exercise, history, sleep_hours)
    if plan:
        return *plan, "stall"

    plan = step_up_after_go_up_reps(exercise, history, sleep_hours)
    if plan:
        return *plan, "step up"

    plan = add_one_rep(exercise, history, sleep_hours)
    return *plan, "+1 rep"


def build_plan(history_by_row, exercise_order, sleep_hours):
    """Return (note_rows, report_rows, skipped_exercises, go_easy).
    note_rows are markdown table lines for the note. report_rows are
    (exercise, weight with arrow, last, aim, rule) for the chat table."""
    skipped_exercises = accessories_to_skip(sleep_hours)
    go_easy = (
        sleep_hours is not None
        and sleep_hours < SLEEP_HOURS_BELOW_WHICH_WEIGHT_AND_REPS_HOLD
    )
    note_rows = [
        "| Exercise | Set | Weight | Reps | RIR |",
        "| --- | --- | --- | --- | --- |",
    ]
    report_rows = []
    for exercise, set_number in exercise_order:
        history = history_by_row.get((exercise, set_number))
        if exercise in skipped_exercises:
            note_rows.append(f"| {exercise} | {set_number} | 0 | | skipped |")
            report_rows.append((exercise, "skip", "", "", "sleep"))
            continue
        if not history:
            note_rows.append(f"| {exercise} | {set_number} | | | pick a weight |")
            report_rows.append((exercise, "?", "none", "", "no history"))
            continue
        last_weight, last_reps = history[0]
        today_weight, today_aim, rule_label = plan_exercise(
            exercise, history, sleep_hours
        )
        note_rows.append(
            f"| {exercise} | {set_number} | {today_weight:g} | | aim {today_aim} |"
        )
        weight_arrow = arrow_for_change(last_weight, today_weight)
        report_rows.append(
            (
                exercise,
                f"{today_weight:g} {weight_arrow}".strip(),
                f"{last_weight:g} x {last_reps}",
                today_aim,
                rule_label,
            )
        )
    note_rows.append(
        "| Jot End Time | 1 | 100 | | JOT END (leave reps empty so i see it) |"
    )
    return note_rows, report_rows, skipped_exercises, go_easy
