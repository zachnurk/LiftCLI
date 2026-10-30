"""Tests each overload rule, the sleep skips, and set handling.
Numbers come from config.example.toml: go up at 7 reps, +2.5 lb for isolation
lifts, +5 lb for compound lifts (Bench Press, Lat Pulldown, Seated Row, Leg
Press), drops keep 95%, stall after 3 sessions, hold under 6 h of sleep."""

import unittest

from src.transform.plan import build_plan, plan_exercise
from src.transform.rules import accessories_to_skip, drop_weight


class TestRules(unittest.TestCase):
    def test_short_sleep_holds_last_weight_and_reps(self):
        """Under 6 h of sleep, repeat last session even if reps were low."""
        self.assertEqual(
            plan_exercise("Bicep Curl", [(30, 3)], 5), (30, 3, "short sleep")
        )

    def test_enough_sleep_does_not_hold(self):
        """6 h or more, or no sleep logged, lets the other rules run."""
        self.assertEqual(plan_exercise("Bicep Curl", [(30, 5)], 6), (30, 6, "+1 rep"))
        self.assertEqual(
            plan_exercise("Bicep Curl", [(30, 5)], None), (30, 6, "+1 rep")
        )

    def test_too_few_reps_drops_weight(self):
        """3 reps is at or below half of 7: drop 5%, rounded to the 2.5 step."""
        self.assertEqual(
            plan_exercise("Bicep Curl", [(30, 3)], None), (27.5, 4, "too few reps")
        )

    def test_four_reps_is_not_too_few(self):
        """4 reps is above half of 7, so no drop."""
        self.assertEqual(
            plan_exercise("Bicep Curl", [(30, 4)], None), (30, 5, "+1 rep")
        )

    def test_stall_drops_weight(self):
        """3 sessions at one weight with no rep gain: drop 5%."""
        history = [(30, 6), (30, 6), (30, 6)]
        self.assertEqual(plan_exercise("Bicep Curl", history, None), (27.5, 7, "stall"))

    def test_rep_gain_is_not_a_stall(self):
        """3 sessions at one weight, but reps went 4, 5, 6: keep going."""
        history = [(30, 6), (30, 5), (30, 4)]
        self.assertEqual(plan_exercise("Bicep Curl", history, None), (30, 7, "+1 rep"))

    def test_two_sessions_are_not_a_stall(self):
        """A stall needs 3 sessions."""
        history = [(30, 6), (30, 6)]
        self.assertEqual(plan_exercise("Bicep Curl", history, None), (30, 7, "+1 rep"))

    def test_isolation_lift_steps_up_2_5(self):
        """7 reps on an isolation lift: +2.5 lb, aim one rep fewer."""
        self.assertEqual(
            plan_exercise("Bicep Curl", [(30, 7)], None), (32.5, 6, "step up")
        )

    def test_compound_lift_steps_up_5(self):
        """7 reps on a compound lift: +5 lb, aim one rep fewer."""
        self.assertEqual(
            plan_exercise("Bench Press", [(135, 7)], None), (140, 6, "step up")
        )

    def test_per_lift_go_up_reps(self):
        """Ab Crunch goes up at 12 reps, not 7."""
        self.assertEqual(
            plan_exercise("Ab Crunch", [(70, 11)], None), (70, 12, "+1 rep")
        )
        self.assertEqual(
            plan_exercise("Ab Crunch", [(70, 12)], None), (72.5, 11, "step up")
        )

    def test_too_few_reps_at_go_up_12(self):
        """Ab Crunch goes up at 12, so 6 reps (half of 12) is too few."""
        self.assertEqual(
            plan_exercise("Ab Crunch", [(70, 6)], None), (67.5, 7, "too few reps")
        )

    def test_seven_reps_is_not_too_few_at_go_up_12(self):
        """7 reps is above half of 12, so no drop."""
        self.assertEqual(plan_exercise("Ab Crunch", [(70, 7)], None), (70, 8, "+1 rep"))

    def test_stall_at_go_up_12(self):
        """3 sessions stuck at 10 reps: drop 5%, aim 11."""
        history = [(70, 10), (70, 10), (70, 10)]
        self.assertEqual(plan_exercise("Ab Crunch", history, None), (67.5, 11, "stall"))

    def test_step_up_past_go_up_aims_one_below_last(self):
        """15 reps on Ab Crunch: +2.5 lb, aim 14 (last reps - 1, not 11)."""
        self.assertEqual(
            plan_exercise("Ab Crunch", [(70, 15)], None), (72.5, 14, "step up")
        )

    def test_otherwise_aim_one_more_rep(self):
        """Below the go-up reps with nothing wrong: same weight, one more rep."""
        self.assertEqual(
            plan_exercise("Bicep Curl", [(30, 5)], None), (30, 6, "+1 rep")
        )

    def test_drop_rounds_to_the_lift_step(self):
        """180 x 0.95 = 171: rounds to 170 for a 5 lb step, 170 for 2.5."""
        self.assertEqual(drop_weight("Bench Press", 180), 170)
        self.assertEqual(drop_weight("Bicep Curl", 180), 170)
        self.assertEqual(drop_weight("Bicep Curl", 30), 27.5)

    def test_accessories_skipped_by_sleep(self):
        """Skip 0 at 7 h, 1 at 6 h, 3 at 5 h, all 5 below that."""
        self.assertEqual(accessories_to_skip(None), [])
        self.assertEqual(accessories_to_skip(7.5), [])
        self.assertEqual(accessories_to_skip(6.5), ["Calf Raise"])
        self.assertEqual(
            accessories_to_skip(5.5), ["Calf Raise", "Leg Curl", "Lateral Raise"]
        )
        self.assertEqual(
            accessories_to_skip(4),
            [
                "Calf Raise",
                "Leg Curl",
                "Lateral Raise",
                "Tricep Pushdown",
                "Bicep Curl",
            ],
        )

    def test_later_sets_copy_the_first_set(self):
        """Set 1 hit 7 reps, set 2 only 3. Both sets get set 1's step up."""
        history_by_row = {("Bicep Curl", 1): [(30, 7)], ("Bicep Curl", 2): [(30, 3)]}
        exercise_order = [("Bicep Curl", 1), ("Bicep Curl", 2)]
        note_rows, report_rows, _, _ = build_plan(history_by_row, exercise_order, None)
        self.assertEqual(note_rows[2], "| Bicep Curl | 1 | 32.5 | | aim 6 |")
        self.assertEqual(note_rows[3], "| Bicep Curl | 2 | 32.5 | | aim 6 |")
        self.assertEqual(len(report_rows), 1)

    def test_lift_with_no_history_asks_for_a_weight(self):
        """A new lift has no weight to plan from."""
        note_rows, _, _, _ = build_plan({}, [("Bicep Curl", 1)], None)
        self.assertEqual(note_rows[2], "| Bicep Curl | 1 | | | pick a weight |")

    def test_skipped_accessory_is_written_as_skipped(self):
        """Under 7 h, Calf Raise is skipped."""
        history_by_row = {("Calf Raise", 1): [(140, 6)]}
        note_rows, _, skipped_exercises, _ = build_plan(
            history_by_row, [("Calf Raise", 1)], 6.5
        )
        self.assertEqual(skipped_exercises, ["Calf Raise"])
        self.assertEqual(note_rows[2], "| Calf Raise | 1 | 0 | | skipped |")


if __name__ == "__main__":
    unittest.main()
