"""Constants for the Monster Remote integration."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "monster_remote"
DEFAULT_PORT = 8765

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SELECT,
]

EVENT_MONSTER_REMOTE = "monster_remote_event"
EVENT_MONSTER_REMOTE_ACTIVITY = "monster_remote_activity"
