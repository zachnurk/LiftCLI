"""Tests reading the notes in test_files: which note --day picks, and that a
lift's history only comes from notes that have that lift.

Each split in test_files has 3 rounds of notes across 2026-09 and 2026-10.
In every day the first lift stalls (same weight and reps), the second gains
up to 8 reps, and the third gains a rep each session (4, 5, 6).
Fullbody also has Ab Crunch (goes up at 12 reps): 9, 11, 13."""

import tempfile
import unittest
from pathlib import Path

from src.extract.lift_notes import read_lift_history

TEST_FILES_DIR = Path(__file__).resolve().parent.parent / "test_files"
TODAY = "2026-11-01"


class TestFullbodyNotes(unittest.TestCase):
    def setUp(self):
        self.notes_dir = TEST_FILES_DIR / "fullbody"

    def test_no_day_picks_the_newest_note(self):
        _, exercise_order, past_note_paths, template_note_path = read_lift_history(
            TODAY, self.notes_dir
        )
        self.assertEqual(len(past_note_paths), 3)
        self.assertEqual(template_note_path.name, "2026-10-02.md")
        self.assertEqual(
            exercise_order,
            [
                ("Bench Press", 1),
                ("Leg Press", 1),
                ("Bicep Curl", 1),
                ("Ab Crunch", 1),
            ],
        )

    def test_history_is_newest_first(self):
        history_by_row, _, _, _ = read_lift_history(TODAY, self.notes_dir)
        self.assertEqual(history_by_row[("Bench Press", 1)], [(135, 6)] * 3)
        self.assertEqual(
            history_by_row[("Leg Press", 1)], [(270, 8), (270, 7), (270, 6)]
        )
        self.assertEqual(history_by_row[("Bicep Curl", 1)], [(30, 6), (30, 5), (30, 4)])
        self.assertEqual(
            history_by_row[("Ab Crunch", 1)], [(70, 13), (70, 11), (70, 9)]
        )


class TestUpperLowerNotes(unittest.TestCase):
    def setUp(self):
        self.notes_dir = TEST_FILES_DIR / "upper_lower"

    def test_no_day_picks_the_newest_note(self):
        _, _, _, template_note_path = read_lift_history(TODAY, self.notes_dir)
        self.assertEqual(template_note_path.name, "2026-10-03.md")

    def test_upper_picks_the_newest_upper_note(self):
        _, exercise_order, _, template_note_path = read_lift_history(
            TODAY, self.notes_dir, "Upper"
        )
        self.assertEqual(template_note_path.name, "2026-10-02.md")
        self.assertEqual(
            exercise_order,
            [("Bench Press", 1), ("Seated Row", 1), ("Bicep Curl", 1)],
        )

    def test_day_name_ignores_case(self):
        _, _, _, template_note_path = read_lift_history(TODAY, self.notes_dir, "upper")
        self.assertEqual(template_note_path.name, "2026-10-02.md")

    def test_upper_history_skips_lower_days(self):
        """3 Upper sessions with a Lower day between each."""
        history_by_row, _, _, _ = read_lift_history(TODAY, self.notes_dir, "Upper")
        self.assertEqual(history_by_row[("Bench Press", 1)], [(135, 6)] * 3)
        self.assertEqual(
            history_by_row[("Seated Row", 1)], [(110, 8), (110, 7), (110, 6)]
        )

    def test_lower_history_skips_upper_days(self):
        history_by_row, _, _, _ = read_lift_history(TODAY, self.notes_dir, "Lower")
        self.assertEqual(history_by_row[("Leg Press", 1)], [(270, 6)] * 3)
        self.assertEqual(
            history_by_row[("Calf Raise", 1)], [(140, 6), (140, 5), (140, 4)]
        )


class TestPushPullLegsNotes(unittest.TestCase):
    def setUp(self):
        self.notes_dir = TEST_FILES_DIR / "push_pull_legs"

    def test_no_day_picks_the_newest_note(self):
        _, _, _, template_note_path = read_lift_history(TODAY, self.notes_dir)
        self.assertEqual(template_note_path.name, "2026-10-04.md")

    def test_push_picks_the_newest_push_note(self):
        _, _, _, template_note_path = read_lift_history(TODAY, self.notes_dir, "Push")
        self.assertEqual(template_note_path.name, "2026-10-02.md")

    def test_pull_picks_the_newest_pull_note(self):
        _, _, _, template_note_path = read_lift_history(TODAY, self.notes_dir, "Pull")
        self.assertEqual(template_note_path.name, "2026-10-03.md")

    def test_seated_row_history_only_from_pull_days(self):
        """Seated Row is only on Pull, so Push and Legs days don't count."""
        history_by_row, _, _, _ = read_lift_history(TODAY, self.notes_dir, "Pull")
        self.assertEqual(
            history_by_row[("Seated Row", 1)], [(110, 8), (110, 7), (110, 6)]
        )

    def test_bench_history_only_from_push_days(self):
        history_by_row, _, _, _ = read_lift_history(TODAY, self.notes_dir, "Push")
        self.assertEqual(history_by_row[("Bench Press", 1)], [(135, 6)] * 3)


class TestEdgeCases(unittest.TestCase):
    def test_unknown_day_finds_no_note(self):
        _, exercise_order, _, template_note_path = read_lift_history(
            TODAY, TEST_FILES_DIR / "upper_lower", "Push"
        )
        self.assertIsNone(template_note_path)
        self.assertEqual(exercise_order, [])

    def test_empty_folder_has_no_notes(self):
        with tempfile.TemporaryDirectory() as empty_dir:
            _, _, past_note_paths, template_note_path = read_lift_history(
                TODAY, Path(empty_dir)
            )
        self.assertEqual(past_note_paths, [])
        self.assertIsNone(template_note_path)

    def test_today_and_later_notes_are_not_history(self):
        """On 2026-10-02 only the two fullbody notes before it count."""
        _, _, past_note_paths, template_note_path = read_lift_history(
            "2026-10-02", TEST_FILES_DIR / "fullbody"
        )
        self.assertEqual(
            [note_path.name for note_path in past_note_paths],
            ["2026-09-30.md", "2026-09-28.md"],
        )
        self.assertEqual(template_note_path.name, "2026-09-30.md")

    def test_skipped_and_blank_rows_are_not_sessions(self):
        """A skipped row (weight 0) and an unlogged row (no reps) are ignored,
        but the lift is still planned."""
        with tempfile.TemporaryDirectory() as temporary_dir:
            month_dir = Path(temporary_dir) / "2026-10"
            month_dir.mkdir()
            (month_dir / "2026-10-01.md").write_text(
                "| Calf Raise | 1 | 140 | 6 | 1 |\n| Leg Curl | 1 | 90 | 6 | 1 |\n"
            )
            (month_dir / "2026-10-03.md").write_text(
                "| Calf Raise | 1 | 0 | | skipped |\n"
                "| Leg Curl | 1 | 92.5 | | aim 7 |\n"
            )
            history_by_row, exercise_order, _, _ = read_lift_history(
                TODAY, Path(temporary_dir)
            )
        self.assertEqual(exercise_order, [("Calf Raise", 1), ("Leg Curl", 1)])
        self.assertEqual(history_by_row[("Calf Raise", 1)], [(140, 6)])
        self.assertEqual(history_by_row[("Leg Curl", 1)], [(90, 6)])


if __name__ == "__main__":
    unittest.main()
