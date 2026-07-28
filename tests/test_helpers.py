"""Tests for pure Monster Remote state helpers."""

import importlib.util
from pathlib import Path


_SPEC = importlib.util.spec_from_file_location(
    "monster_remote_helpers",
    Path(__file__).parents[1]
    / "custom_components"
    / "monster_remote"
    / "helpers.py",
)
assert _SPEC is not None and _SPEC.loader is not None
_HELPERS = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_HELPERS)

current_action = _HELPERS.current_action
current_screen = _HELPERS.current_screen
exercise_name = _HELPERS.exercise_name
load_state = _HELPERS.load_state
session_metrics = _HELPERS.session_metrics
session_state = _HELPERS.session_state
timestamp = _HELPERS.timestamp
workout_active = _HELPERS.workout_active


def test_free_action_follows_active_screen():
    data = {
        "state": {
            "current_screen": "/free_training",
            "free_exercise_json": {"title": "Bicep Curl"},
            "course_exercise_json": {"title": "Wrong Course Action"},
        }
    }
    assert current_screen(data) == "/free_training"
    assert current_action(data)["title"] == "Bicep Curl"
    assert exercise_name(data) == "Bicep Curl"
    assert workout_active(data)


def test_home_is_not_training():
    assert not workout_active({"state": {"current_screen": "/home"}})


def test_normalized_state_wins_over_legacy_fields():
    data = {
        "state": {
            "current_screen": "/home",
            "session_state": {
                "active": True,
                "screen": "/course_player",
                "exercise": "Rowing",
            },
            "load_state": {"weight": 42, "unit": "kg"},
            "session_metrics": {"reps": 12, "sets": 2, "volume": 504},
        }
    }
    assert workout_active(data)
    assert exercise_name(data) == "Rowing"
    assert load_state(data)["weight"] == 42
    assert session_metrics(data)["volume"] == 504
    assert session_state(data)["screen"] == "/course_player"


def test_timestamp_uses_unix_milliseconds():
    value = timestamp(1_700_000_000_000)
    assert value is not None
    assert value.tzinfo is not None
    assert int(value.timestamp()) == 1_700_000_000
