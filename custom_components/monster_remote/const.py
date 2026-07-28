"""Constants for the Monster Remote integration."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "monster_remote"
DEFAULT_NAME = "Gym Monster"
DEFAULT_PORT = 8765
DEFAULT_SECRET = "lilaq-monster-9f3a2c7e1b"

CONF_SECRET = "secret"

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SELECT,
]

EVENT_MONSTER_REMOTE = "monster_remote_event"
