"""Loads every setting plan_lift uses. Don't edit this file.
Training numbers live in config.toml (copy config.example.toml to start one).
Machine-specific values (Google Health credentials, LIFTING_DIR) live in .env
(copy .env.example). Both are gitignored."""

import os
import tomllib
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
ENV_FILE_PATH = REPO_DIR / ".env"
# LIFT_PLANNER_CONFIG points at another config file. The tests use it.
CONFIG_FILE_PATH = Path(os.environ.get("LIFT_PLANNER_CONFIG", REPO_DIR / "config.toml"))
EXAMPLE_CONFIG_FILE_PATH = REPO_DIR / "config.example.toml"


def read_env_file():
    """Return the KEY=value lines of .env as a dict, skipping comments. Empty if
    there's no .env."""
    if not ENV_FILE_PATH.exists():
        return {}
    env_values = {}
    for env_line in ENV_FILE_PATH.read_text().splitlines():
        if env_line.strip() and not env_line.startswith("#"):
            env_key, env_value = env_line.split("=", 1)
            env_values[env_key.strip()] = env_value.strip()
    return env_values


def read_config_file():
    """Return config.toml as a dict, or config.example.toml if there's no
    config.toml yet."""
    config_path = (
        CONFIG_FILE_PATH if CONFIG_FILE_PATH.exists() else EXAMPLE_CONFIG_FILE_PATH
    )
    with config_path.open("rb") as config_file:
        return tomllib.load(config_file)


ENV_VALUES = read_env_file()
CONFIG_VALUES = read_config_file()

# Default folder of lift notes (YYYY-MM/YYYY-MM-DD.md), from LIFTING_DIR in .env.
# None means --input-dir and --output-dir are required.
LIFTING_DIR = (
    Path(ENV_VALUES["LIFTING_DIR"]).expanduser()
    if "LIFTING_DIR" in ENV_VALUES
    else None
)

DEFAULT_REPS_NEEDED_TO_ADD_WEIGHT = CONFIG_VALUES["default_reps_needed_to_add_weight"]
REPS_TO_GO_UP = CONFIG_VALUES["reps_to_go_up"]
DEFAULT_WEIGHT_INCREASE_LB = CONFIG_VALUES["default_weight_increase_lb"]
COMPOUND_LIFTS = CONFIG_VALUES["compound_lifts"]
COMPOUND_WEIGHT_INCREASE_LB = CONFIG_VALUES["compound_weight_increase_lb"]
WEIGHT_STEP = CONFIG_VALUES["weight_step"]
SHARE_OF_WEIGHT_KEPT_AFTER_DROP = CONFIG_VALUES["share_of_weight_kept_after_drop"]
SHARE_OF_GO_UP_REPS_THAT_TRIGGERS_DROP = CONFIG_VALUES[
    "share_of_go_up_reps_that_triggers_drop"
]
SESSIONS_WITHOUT_REP_GAIN_BEFORE_STALL_DROP = CONFIG_VALUES[
    "sessions_without_rep_gain_before_stall_drop"
]
SLEEP_HOURS_BELOW_WHICH_WEIGHT_AND_REPS_HOLD = CONFIG_VALUES[
    "sleep_hours_below_which_weight_and_reps_hold"
]
DROP_ORDER = CONFIG_VALUES["drop_order"]
ACCESSORIES_SKIPPED_BY_MINIMUM_SLEEP_HOURS = CONFIG_VALUES[
    "accessories_skipped_by_minimum_sleep_hours"
]
HOURS_BACK_TO_SEARCH_FOR_LAST_NIGHTS_SLEEP = CONFIG_VALUES[
    "hours_back_to_search_for_last_nights_sleep"
]
