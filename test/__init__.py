"""Every test runs against config.example.toml, so the expected numbers don't
depend on anyone's config.toml. plan_lift.py runs in the end-to-end tests
inherit this too."""

import os
from pathlib import Path

os.environ["LIFTCLI_CONFIG"] = str(
    Path(__file__).resolve().parent.parent / "config.example.toml"
)
