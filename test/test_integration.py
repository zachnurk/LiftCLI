"""End to end: run plan_lift.py on a copy of each split in test_files and check
the exact note it writes.

Expected weights, from config.example.toml:
- First lift stalled at 6 reps: drop 5%. 135 -> 130, 270 -> 255, 120 -> 115.
- Second lift hit 8 reps: step up, aim 6 (go-up 7 - 1). +5 for compound
  lifts, +2.5 otherwise.
- Third lift is at 6 reps: same weight, aim 7.
- Fullbody's Ab Crunch goes up at 12 and hit 13: +2.5, aim 11."""

import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from src.extract.lift_notes import read_lift_history

REPO_DIR = Path(__file__).resolve().parent.parent
TEMPORARY_DIR = tempfile.TemporaryDirectory()


def tearDownModule():
    TEMPORARY_DIR.cleanup()


def plan_today(split_folder, *extra_arguments, sleep_hours=8):
    """Copy test_files/split_folder to a new temp folder, run plan_lift.py on
    it, and return (notes_dir, path of today's note, today's note text)."""
    notes_dir = Path(tempfile.mkdtemp(dir=TEMPORARY_DIR.name)) / split_folder
    shutil.copytree(REPO_DIR / "test_files" / split_folder, notes_dir)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "src.plan_lift",
            "--sleep",
            str(sleep_hours),
            "--input-dir",
            str(notes_dir),
            "--output-dir",
            str(notes_dir),
            *extra_arguments,
        ],
        check=True,
        capture_output=True,
        cwd=REPO_DIR,
    )
    today = datetime.now().astimezone().date().isoformat()
    today_note_path = notes_dir / today[:7] / f"{today}.md"
    return notes_dir, today_note_path, today_note_path.read_text()


def table_rows(note_text):
    """The note's exercise rows, without the header and the end-time row."""
    return [
        line
        for line in note_text.splitlines()
        if line.startswith("| ")
        and not line.startswith(("| Exercise", "| ---", "| Jot End Time"))
    ]


class TestFullbody(unittest.TestCase):
    def test_plans_fullbody(self):
        _, _, note_text = plan_today("fullbody")
        self.assertIn("# Fullbody", note_text)
        self.assertEqual(
            table_rows(note_text),
            [
                "| Bench Press | 1 | 130 | | aim 7 |",
                "| Leg Press | 1 | 275 | | aim 6 |",
                "| Bicep Curl | 1 | 30 | | aim 7 |",
                "| Ab Crunch | 1 | 72.5 | | aim 11 |",
            ],
        )


class TestUpperLower(unittest.TestCase):
    def test_plans_upper(self):
        _, _, note_text = plan_today("upper_lower", "--day", "Upper")
        self.assertIn("# Upper", note_text)
        self.assertEqual(
            table_rows(note_text),
            [
                "| Bench Press | 1 | 130 | | aim 7 |",
                "| Seated Row | 1 | 115 | | aim 6 |",
                "| Bicep Curl | 1 | 30 | | aim 7 |",
            ],
        )

    def test_plans_lower(self):
        _, _, note_text = plan_today("upper_lower", "--day", "Lower")
        self.assertIn("# Lower", note_text)
        self.assertEqual(
            table_rows(note_text),
            [
                "| Leg Press | 1 | 255 | | aim 7 |",
                "| Leg Curl | 1 | 92.5 | | aim 6 |",
                "| Calf Raise | 1 | 140 | | aim 7 |",
            ],
        )

    def test_no_day_plans_the_newest_note(self):
        """The newest note is Lower, so that's what gets planned."""
        _, _, note_text = plan_today("upper_lower")
        self.assertIn("# Lower", note_text)

    def test_logged_note_is_read_back_as_history(self):
        """Log the planned Upper note as done, then plan Upper tomorrow."""
        notes_dir, today_note_path, note_text = plan_today(
            "upper_lower", "--day", "Upper"
        )
        today_note_path.write_text(
            note_text.replace("| 130 | | aim 7 |", "| 130 | 7 | 1 |")
        )
        tomorrow = (datetime.now().astimezone().date() + timedelta(days=1)).isoformat()
        history_by_row, _, _, template_note_path = read_lift_history(
            tomorrow, notes_dir, "Upper"
        )
        self.assertEqual(template_note_path, today_note_path)
        self.assertEqual(
            history_by_row[("Bench Press", 1)], [(130, 7), (135, 6), (135, 6), (135, 6)]
        )


class TestPushPullLegs(unittest.TestCase):
    def test_plans_push(self):
        _, _, note_text = plan_today("push_pull_legs", "--day", "Push")
        self.assertIn("# Push", note_text)
        self.assertEqual(
            table_rows(note_text),
            [
                "| Bench Press | 1 | 130 | | aim 7 |",
                "| Shoulder Press | 1 | 87.5 | | aim 6 |",
                "| Tricep Pushdown | 1 | 50 | | aim 7 |",
            ],
        )

    def test_plans_pull(self):
        _, _, note_text = plan_today("push_pull_legs", "--day", "Pull")
        self.assertIn("# Pull", note_text)
        self.assertEqual(
            table_rows(note_text),
            [
                "| Lat Pulldown | 1 | 115 | | aim 7 |",
                "| Seated Row | 1 | 115 | | aim 6 |",
                "| Bicep Curl | 1 | 30 | | aim 7 |",
            ],
        )

    def test_plans_legs(self):
        _, _, note_text = plan_today("push_pull_legs", "--day", "Legs")
        self.assertIn("# Legs", note_text)
        self.assertEqual(
            table_rows(note_text),
            [
                "| Leg Press | 1 | 255 | | aim 7 |",
                "| Leg Curl | 1 | 92.5 | | aim 6 |",
                "| Calf Raise | 1 | 140 | | aim 7 |",
            ],
        )

    def test_no_day_plans_the_newest_note(self):
        """The newest note is Legs, so that's what gets planned."""
        _, _, note_text = plan_today("push_pull_legs")
        self.assertIn("# Legs", note_text)


class TestShortSleep(unittest.TestCase):
    def test_short_sleep_holds_and_skips_accessories(self):
        """5.5 h: hold every lift and skip Calf Raise and Leg Curl."""
        _, _, note_text = plan_today("upper_lower", "--day", "Lower", sleep_hours=5.5)
        self.assertEqual(
            table_rows(note_text),
            [
                "| Leg Press | 1 | 270 | | aim 6 |",
                "| Leg Curl | 1 | 0 | | skipped |",
                "| Calf Raise | 1 | 0 | | skipped |",
            ],
        )


if __name__ == "__main__":
    unittest.main()
