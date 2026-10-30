"""Extract: past sessions and today's exercise order from the lift notes."""

import re

from src.settings import SESSIONS_WITHOUT_REP_GAIN_BEFORE_STALL_DROP

LIFT_ROW_PATTERN = re.compile(
    r"^\|([^|]+)\|\s*(\d+)\s*\|\s*([\d.]*)\s*\|\s*(\d*)\s*\|([^|]*)\|", re.MULTILINE
)
# Frontmatter line holding hours slept, e.g. "sleep: 7.2".
SLEEP_PROPERTY_PATTERN = re.compile(r"^sleep:\s*([\d.]+)\s*$", re.MULTILINE)
# The note's day name, e.g. "# Upper".
DAY_HEADING_PATTERN = re.compile(r"^# (.+)$", re.MULTILINE)
# Row plan_lift adds at the end of every note, so it's not an exercise.
END_TIME_ROW_EXERCISE = "Jot End Time"


def read_lift_rows(note_text):
    """Return the note's exercise rows as ((exercise, set number), weight, reps),
    with weight and reps as strings, blank if not logged."""
    lift_rows = []
    for exercise, set_number, weight, reps, _ in LIFT_ROW_PATTERN.findall(note_text):
        row_key = (exercise.strip(), int(set_number))
        if row_key[0] != END_TIME_ROW_EXERCISE:
            lift_rows.append((row_key, weight, reps))
    return lift_rows


def read_day_heading(note_text):
    """Return the note's "# Day" heading text, or None if it has none."""
    heading_match = DAY_HEADING_PATTERN.search(note_text)
    return heading_match.group(1).strip() if heading_match else None


def read_lift_history(today, input_dir, day_name=None):
    """Return (history_by_row, exercise_order, past_note_paths, template_note_path).
    template_note_path is the newest past note, or with day_name the newest one
    whose heading matches it (any case). None if there's no such note.
    exercise_order is the (exercise, set number) rows of that note, in order.
    history_by_row maps (exercise, set number) to its real sessions (weight and
    reps logged) as (weight, reps) tuples, newest first, from every note that
    has that row, whatever its day. The note column is ignored on purpose: the
    plan is weight and reps only. past_note_paths is newest first. Reading
    stops once every exercise has enough sessions for the stall check, since
    older ones are never used."""
    past_note_paths = sorted(
        (path for path in input_dir.glob("*/*.md") if path.name < f"{today}.md"),
        key=lambda note_path: note_path.name,
        reverse=True,
    )
    template_note_path = next(
        (
            note_path
            for note_path in past_note_paths
            if day_name is None
            or (read_day_heading(note_path.read_text()) or "").lower()
            == day_name.lower()
        ),
        None,
    )
    if template_note_path is None:
        return {}, [], past_note_paths, None
    exercise_order = [
        row_key for row_key, _, _ in read_lift_rows(template_note_path.read_text())
    ]
    history_by_row = {}
    for note_path in past_note_paths:
        for row_key, weight, reps in read_lift_rows(note_path.read_text()):
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
    return history_by_row, exercise_order, past_note_paths, template_note_path


def read_sleep_property(note_path):
    """Return the hours in a note's sleep property, or None if it's blank or
    the note doesn't exist."""
    if not note_path.exists():
        return None
    sleep_match = SLEEP_PROPERTY_PATTERN.search(note_path.read_text())
    return float(sleep_match.group(1)) if sleep_match else None
