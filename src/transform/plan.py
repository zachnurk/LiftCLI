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


def build_plan(history_by_row, exercise_order, sleep_hours, adjustment_by_row):
    """Return (note_rows, report_rows, skipped_exercises, go_easy).
    note_rows are markdown table lines for the note: RIR is left blank to log,
    Adj. carries over from adjustment_by_row, and Notes holds the aim. report_rows are
    (exercise, weight with arrow, last, aim, rule) for the chat table, one per
    exercise. The rules run on each exercise's first set only. Later sets copy
    its weight and aim (straight sets)."""
    skipped_exercises = accessories_to_skip(sleep_hours)
    go_easy = (
        sleep_hours is not None
        and sleep_hours < SLEEP_HOURS_BELOW_WHICH_WEIGHT_AND_REPS_HOLD
    )
    note_rows = [
        "| Exercise | Set | Weight | Reps | RIR | Adj. | Notes |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    report_rows = []
    weight_and_notes_by_exercise = {}
    for exercise, set_number in exercise_order:
        if exercise not in weight_and_notes_by_exercise:
            history = history_by_row.get((exercise, set_number))
            if exercise in skipped_exercises:
                weight_and_notes_by_exercise[exercise] = ("0", "skipped")
                report_rows.append((exercise, "skip", "", "", "sleep"))
            elif not history:
                weight_and_notes_by_exercise[exercise] = ("", "pick a weight")
                report_rows.append((exercise, "?", "none", "", "no history"))
            else:
                last_weight, last_reps = history[0]
                today_weight, today_aim, rule_label = plan_exercise(
                    exercise, history, sleep_hours
                )
                weight_and_notes_by_exercise[exercise] = (
                    f"{today_weight:g}",
                    f"aim {today_aim}",
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
        weight_cell, notes_cell = weight_and_notes_by_exercise[exercise]
        adjustment_cell = adjustment_by_row.get((exercise, set_number), "")
        row_cells = [
            exercise,
            str(set_number),
            weight_cell,
            "",
            "",
            adjustment_cell,
            notes_cell,
        ]
        note_rows.append(
            "|" + "|".join(f" {cell} " if cell else " " for cell in row_cells) + "|"
        )
    note_rows.append(
        "| Jot End Time | 1 | 100 | | | | JOT END (leave reps empty so i see it) |"
    )
    return note_rows, report_rows, skipped_exercises, go_easy
