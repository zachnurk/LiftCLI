"""Extract: last night's sleep from the Google Health API
(https://health.googleapis.com). Credentials come from .env. Optional: without
working credentials the sleep property in today's note is used instead."""

import json
import urllib.parse
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path

from src.settings import ENV_VALUES, HOURS_BACK_TO_SEARCH_FOR_LAST_NIGHTS_SLEEP

GOOGLE_HEALTH_API_BASE_URL = "https://health.googleapis.com/v4/users/me/dataTypes"
GOOGLE_OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"


def get_access_token():
    """Trade the refresh token (shared with the google-health MCP) for a fresh
    access token."""
    token_file_path = Path(ENV_VALUES["GOOGLE_HEALTH_TOKEN_PATH"]).expanduser()
    refresh_token = json.loads(token_file_path.read_text())["refresh_token"]
    token_request_body = urllib.parse.urlencode(
        {
            "client_id": ENV_VALUES["GOOGLE_HEALTH_CLIENT_ID"],
            "client_secret": ENV_VALUES["GOOGLE_HEALTH_CLIENT_SECRET"],
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
    ).encode()
    with urllib.request.urlopen(GOOGLE_OAUTH_TOKEN_URL, token_request_body) as response:
        return json.load(response)["access_token"]


def list_data_points(access_token, data_type, page_size):
    """Return the newest data points of one data type."""
    data_points_request = urllib.request.Request(
        f"{GOOGLE_HEALTH_API_BASE_URL}/{data_type}/dataPoints?pageSize={page_size}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    with urllib.request.urlopen(data_points_request) as response:
        return json.load(response).get("dataPoints", [])


def fetch_sleep_hours():
    """Return hours asleep in the lookback window, rounded to 0.1. Returns None
    if .env is missing, the credentials fail, or no sleep has synced."""
    try:
        access_token = get_access_token()
        sleep_points = list_data_points(access_token, "sleep", 10)
    except (OSError, KeyError, ValueError):
        return None
    sleep_window_start = datetime.now(UTC) - timedelta(
        hours=HOURS_BACK_TO_SEARCH_FOR_LAST_NIGHTS_SLEEP
    )
    sleep_minutes = sum(
        int(sleep_point["sleep"]["summary"]["minutesAsleep"])
        for sleep_point in sleep_points
        if datetime.fromisoformat(sleep_point["sleep"]["interval"]["endTime"])
        >= sleep_window_start
    )
    if not sleep_minutes:
        return None
    return round(sleep_minutes / 60, 1)
