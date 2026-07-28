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
