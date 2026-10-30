"""Extract: past sessions and today's exercise order from the lift notes."""

import re

from src.settings import SESSIONS_WITHOUT_REP_GAIN_BEFORE_STALL_DROP

LIFT_ROW_PATTERN = re.compile(
    r"^\|([^|]+)\|\s*(\d+)\s*\|\s*([\d.]*)\s*\|\s*(\d*)\s*\|([^|]*)\|", re.MULTILINE
)
# Frontmatter line holding hours slept, e.g. "sleep: 7.2".
SLEEP_PROPERTY_PATTERN = re.compile(r"^sleep:\s*([\d.]+)\s*$", re.MULTILINE)
# Row plan_lift adds at the end of every note, so it's not an exercise.
END_TIME_ROW_EXERCISE = "Jot End Time"


def read_lift_history(today, input_dir):
    """Return (history_by_row, exercise_order, past_note_paths).
    history_by_row maps (exercise, set number) to its real sessions (weight and
    reps logged) as (weight, reps) tuples, newest first. The note column is
    ignored on purpose: the plan is weight and reps only. exercise_order is the
    (exercise, set number) rows of the newest note, in order.
    past_note_paths is newest first. Reading stops once every exercise has
    enough sessions for the stall check, since older ones are never used."""
    past_note_paths = sorted(
        (path for path in input_dir.glob("*/*.md") if path.name < f"{today}.md"),
        reverse=True,
    )
    history_by_row = {}
    exercise_order = []
    for note_path in past_note_paths:
        for exercise, set_number, weight, reps, _ in LIFT_ROW_PATTERN.findall(
            note_path.read_text()
        ):
            row_key = (exercise.strip(), int(set_number))
            if row_key[0] == END_TIME_ROW_EXERCISE:
                continue
            if note_path == past_note_paths[0]:
                exercise_order.append(row_key)
            if weight and reps and float(weight) > 0 and int(reps) > 0:
                history_by_row.setdefault(row_key, []).append(
                    (float(weight), int(reps))
                )
        every_exercise_has_enough_sessions = all(
            len(history_by_row.get(row_key, []))
            >= SESSIONS_WITHOUT_REP_GAIN_BEFORE_STALL_DROP
            for row_key in exercise_order
        )
        if every_exercise_has_enough_sessions:
            break
    return history_by_row, exercise_order, past_note_paths


def read_sleep_property(note_path):
    """Return the hours in a note's sleep property, or None if it's blank or
    the note doesn't exist."""
    if not note_path.exists():
        return None
    sleep_match = SLEEP_PROPERTY_PATTERN.search(note_path.read_text())
    return float(sleep_match.group(1)) if sleep_match else None
