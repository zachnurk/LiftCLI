"""The overload rules, one function per rule. Each rule takes an exercise, its
past sessions (newest first, as (weight, reps) tuples), and last night's
sleep, then returns (today_weight, today_aim) or None if it doesn't apply.
plan_exercise in src/transform/plan.py calls them in priority order.

Citation keys like [knowles2018] point to docs/references.bib."""

from src.settings import (
    ACCESSORIES_SKIPPED_BY_MINIMUM_SLEEP_HOURS,
    COMPOUND_LIFTS,
    COMPOUND_WEIGHT_INCREASE_LB,
    DEFAULT_REPS_NEEDED_TO_ADD_WEIGHT,
    DEFAULT_WEIGHT_INCREASE_LB,
    DROP_ORDER,
    REPS_TO_GO_UP,
    SESSIONS_WITHOUT_REP_GAIN_BEFORE_STALL_DROP,
    SHARE_OF_GO_UP_REPS_THAT_TRIGGERS_DROP,
    SHARE_OF_WEIGHT_KEPT_AFTER_DROP,
    SLEEP_HOURS_BELOW_WHICH_WEIGHT_AND_REPS_HOLD,
    WEIGHT_STEP,
)


def accessories_to_skip(sleep_hours):
    """Skip the last accessories in drop_order on short sleep, per
    ACCESSORIES_SKIPPED_BY_MINIMUM_SLEEP_HOURS. Main lifts are never skipped.

    Source: [craven2022]. Performance drops after one short night, so trim volume
    instead of pushing. The hour cutoffs and skip counts are my own, not from
    the study. No sleep logged means nothing is skipped."""
    if sleep_hours is None:
        return []
    for (
        minimum_sleep_hours,
        number_to_skip,
    ) in ACCESSORIES_SKIPPED_BY_MINIMUM_SLEEP_HOURS:
        if sleep_hours >= minimum_sleep_hours:
            return DROP_ORDER[:number_to_skip]
    return DROP_ORDER


def hold_on_short_sleep(exercise, history, sleep_hours):
    """Under SLEEP_HOURS_BELOW_WHICH_WEIGHT_AND_REPS_HOLD of sleep: keep last
    weight and match last reps.

    Source: [knowles2018]. Sleep loss cuts strength on multi-joint lifts, so a PR
    attempt that day is noise. Doesn't apply when no sleep is logged."""
    last_weight, last_reps = history[0]
    if sleep_hours is None:
        return None
    if sleep_hours >= SLEEP_HOURS_BELOW_WHICH_WEIGHT_AND_REPS_HOLD:
        return None
    return last_weight, last_reps


def drop_when_reps_far_below_range(exercise, history, sleep_hours):
    """Last set reached SHARE_OF_GO_UP_REPS_THAT_TRIGGERS_DROP of the go-up reps
    or fewer: drop the weight, aim last reps + 1. Adapts to each lift's
    reps_to_go_up.

        go-up 7:   drop at 3 reps or fewer
        go-up 12:  drop at 6 reps or fewer"""
    last_weight, last_reps = history[0]
    go_up_reps = REPS_TO_GO_UP.get(exercise, DEFAULT_REPS_NEEDED_TO_ADD_WEIGHT)
    too_few_reps = go_up_reps * SHARE_OF_GO_UP_REPS_THAT_TRIGGERS_DROP
    if last_reps > too_few_reps:
        return None
    return drop_weight(exercise, last_weight), last_reps + 1


def drop_after_stall(exercise, history, sleep_hours):
    """SESSIONS_WITHOUT_REP_GAIN_BEFORE_STALL_DROP sessions in a row at one
    weight, with the newest reps no better than the oldest: drop the weight, aim
    last reps + 1.

    Sources: [startingstrength_reset] and [legion_deload] use about three missed
    sessions before a reset. A program convention, not a research finding."""
    if len(history) < SESSIONS_WITHOUT_REP_GAIN_BEFORE_STALL_DROP:
        return None
    stall_window = history[:SESSIONS_WITHOUT_REP_GAIN_BEFORE_STALL_DROP]
    newest_weight, newest_reps = stall_window[0]
    _, oldest_reps = stall_window[-1]
    same_weight_every_session = all(
        weight == newest_weight for weight, _ in stall_window
    )
    no_rep_gain = newest_reps <= oldest_reps
    if not (same_weight_every_session and no_rep_gain):
        return None
    return drop_weight(exercise, newest_weight), newest_reps + 1


def weight_step_for(exercise):
    """The lift's weight step in lb: its weight_step entry if it has one, else
    the compound step for compound_lifts, else the default isolation step.
    Compounds spread the load over more muscle, so they take a bigger jump."""
    if exercise in WEIGHT_STEP:
        return WEIGHT_STEP[exercise]
    if exercise in COMPOUND_LIFTS:
        return COMPOUND_WEIGHT_INCREASE_LB
    return DEFAULT_WEIGHT_INCREASE_LB


def step_up_after_go_up_reps(exercise, history, sleep_hours):
    """Hit the go-up reps (reps_to_go_up, else DEFAULT_REPS_NEEDED_TO_ADD_WEIGHT):
    add one weight step (see weight_step_for), aim one rep fewer.

    Source: [acsm2009] for adding load once you beat the target reps. The steps
    are small (often under ACSM's 2-10%) to prevent ego lifting and strain."""
    last_weight, last_reps = history[0]
    go_up_reps = REPS_TO_GO_UP.get(exercise, DEFAULT_REPS_NEEDED_TO_ADD_WEIGHT)
    if last_reps < go_up_reps:
        return None
    weight_step = weight_step_for(exercise)
    today_weight = last_weight + weight_step
    today_aim = last_reps - 1
    return today_weight, today_aim


def add_one_rep(exercise, history, sleep_hours):
    """Otherwise: same weight, aim last reps + 1.

    Source: [repstack_double_progression]. Add reps at a fixed weight until the
    top of the range, then add weight."""
    last_weight, last_reps = history[0]
    return last_weight, last_reps + 1


def drop_weight(exercise, weight):
    """Multiply by SHARE_OF_WEIGHT_KEPT_AFTER_DROP and round to the lift's weight
    step so the plates exist.
    Example at 5%: 180 with a 2.5 step becomes 171, rounded to 170.

    Source: no study has tested a drop size. [bell2023] coaches agreed deloads
    lower load or effort but gave no number. 5% is my choice for an
    advanced lifter."""
    weight_step = weight_step_for(exercise)
    dropped_weight = weight * SHARE_OF_WEIGHT_KEPT_AFTER_DROP
    return round(dropped_weight / weight_step) * weight_step
