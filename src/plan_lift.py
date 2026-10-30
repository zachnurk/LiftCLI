"""Plan today's lift.
Run from the repo folder:
python3 -m src.plan_lift [--day NAME] [--sleep HOURS] [--input-dir DIR]
[--output-dir DIR] [--force]

Extract (src/extract/), transform (src/transform/, rules in rules.py), write
(src/write/). Training settings live in config.toml, credentials and LIFTING_DIR
in .env. Sources for every rule are in docs/references.bib."""

import argparse
import sys
from datetime import datetime
from pathlib import Path

from src.extract.google_health import fetch_sleep_hours
from src.extract.lift_notes import (
    read_day_heading,
    read_lift_history,
    read_sleep_property,
)
from src.settings import LIFTING_DIR
from src.transform.plan import build_plan
from src.write.note import write_note
from src.write.report import print_report

argument_parser = argparse.ArgumentParser(description="Plan today's lift.")
argument_parser.add_argument(
    "--input-dir",
    type=Path,
    default=LIFTING_DIR,
    required=LIFTING_DIR is None,
    help="folder of past lift notes (YYYY-MM/YYYY-MM-DD.md)",
)
argument_parser.add_argument(
    "--output-dir",
    type=Path,
    default=LIFTING_DIR,
    required=LIFTING_DIR is None,
    help="folder to write today's note into, under YYYY-MM/",
)
argument_parser.add_argument(
    "--sleep",
    type=float,
    help="hours slept last night; skips Google Health and the sleep property",
)
argument_parser.add_argument(
    "--day",
    help="plan from the newest note with this # heading, e.g. Lower "
    "(default: the newest note)",
)
argument_parser.add_argument(
    "--force", action="store_true", help="overwrite today's note"
)
parsed_arguments = argument_parser.parse_args()
input_dir = parsed_arguments.input_dir.expanduser()
output_dir = parsed_arguments.output_dir.expanduser()

today = datetime.now().astimezone().date().isoformat()
today_note_path = output_dir / today[:7] / f"{today}.md"
today_note_has_plan = (
    today_note_path.exists() and "| Exercise |" in today_note_path.read_text()
)
if today_note_has_plan and not parsed_arguments.force:
    sys.exit(f"{today_note_path} has a plan. Rerun with --force to replace it.")

history_by_row, exercise_order, past_note_paths, template_note_path = read_lift_history(
    today, input_dir, parsed_arguments.day
)
if not past_note_paths:
    sys.exit(f"No past lift notes in {input_dir}. Log one session first.")
if template_note_path is None:
    sys.exit(f"No past note in {input_dir} has the heading # {parsed_arguments.day}.")
if not exercise_order:
    sys.exit(f"{template_note_path} has no exercise rows to plan from.")
day_heading = read_day_heading(template_note_path.read_text()) or "Lift"
sleep_hours = parsed_arguments.sleep
sleep_source = "--sleep"
if sleep_hours is None:
    sleep_hours = fetch_sleep_hours()
    sleep_source = "Google Health"
if sleep_hours is None:
    sleep_hours = read_sleep_property(today_note_path)
    sleep_source = "sleep property"
if sleep_hours is None:
    print("Sleep: not logged, sleep rules skipped.")
else:
    print(f"Sleep: {sleep_hours:g}h from {sleep_source}.")

note_rows, report_rows, skipped_exercises, go_easy = build_plan(
    history_by_row, exercise_order, sleep_hours
)

write_note(
    today_note_path,
    day_heading,
    note_rows,
    sleep_hours,
    skipped_exercises,
    go_easy,
)
print_report(today_note_path, report_rows)
