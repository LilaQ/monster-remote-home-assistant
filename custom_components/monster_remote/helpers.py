"""Pure helpers for interpreting retained Monster Remote state."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any

TRAINING_SCREENS = ("free_training", "course_player")


def as_dict(value: Any) -> dict[str, Any]:
    """Return value as a dictionary."""
    return value if isinstance(value, dict) else {}


def nested_value(value: Any, names: Iterable[str]) -> Any:
    """Find the first matching field recursively."""
    if isinstance(value, dict):
        for name in names:
            if name in value and value[name] not in (None, ""):
                return value[name]
        for child in value.values():
            found = nested_value(child, names)
            if found not in (None, ""):
                return found
    elif isinstance(value, list):
        for child in value:
            found = nested_value(child, names)
            if found not in (None, ""):
                return found
    return None


def number(value: Any) -> float | None:
    """Convert a JSON value to a finite float."""
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if result != result or result in (float("inf"), float("-inf")):
        return None
    return result


def integer(value: Any) -> int | None:
    """Convert a JSON value to an integer."""
    parsed = number(value)
    return int(parsed) if parsed is not None else None


def retained(data: dict[str, Any]) -> dict[str, Any]:
    """Return the retained watch state."""
    return as_dict(data.get("state"))


def session_state(data: dict[str, Any]) -> dict[str, Any]:
    """Return the normalized session snapshot."""
    return as_dict(retained(data).get("session_state"))


def load_state(data: dict[str, Any]) -> dict[str, Any]:
    """Return the normalized load snapshot."""
    return as_dict(retained(data).get("load_state"))


def session_metrics(data: dict[str, Any]) -> dict[str, Any]:
    """Return normalized current-session counters."""
    return as_dict(retained(data).get("session_metrics"))


def timestamp(value: Any) -> datetime | None:
    """Convert a Unix millisecond timestamp to a UTC datetime."""
    parsed = number(value)
    if parsed is None or parsed <= 0:
        return None
    return datetime.fromtimestamp(parsed / 1000.0, tz=timezone.utc)


def current_screen(data: dict[str, Any]) -> str:
    """Return the current Speediance route."""
    normalized = session_state(data).get("screen")
    return str(normalized or retained(data).get("current_screen", "") or "")


def workout_active(data: dict[str, Any]) -> bool:
    """Return whether a supported workout screen is active."""
    normalized = session_state(data)
    if "active" in normalized:
        return bool(normalized.get("active"))
    screen = current_screen(data)
    return any(name in screen for name in TRAINING_SCREENS)


def current_action(data: dict[str, Any]) -> dict[str, Any]:
    """Return the action belonging to the active screen."""
    state = retained(data)
    screen = current_screen(data)
    preferred = (
        "free_exercise_json"
        if "free_training" in screen
        else "course_exercise_json"
    )
    action = as_dict(state.get(preferred))
    if action:
        return action
    return as_dict(
        state.get("course_exercise_json")
        or state.get("free_exercise_json")
    )


def exercise_name(data: dict[str, Any]) -> str | None:
    """Return the current exercise title."""
    normalized = session_state(data).get("exercise")
    if normalized not in (None, ""):
        return str(normalized)
    value = nested_value(
        current_action(data),
        ("title", "actionName", "name"),
    )
    return str(value) if value not in (None, "") else None


def resistance_event(data: dict[str, Any], kind: str | None = None) -> dict[str, Any]:
    """Return the latest matching resistance event."""
    event = as_dict(retained(data).get("live_resistance"))
    if kind is None or event.get("kind") == kind:
        return event
    return {}


def rounded(value: Any, digits: int = 1) -> float | int | None:
    """Return a compact numeric state."""
    parsed = number(value)
    if parsed is None:
        return None
    result = round(parsed, digits)
    return int(result) if result.is_integer() else result
