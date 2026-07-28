"""Binary sensor platform for Monster Remote."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import MonsterRemoteCoordinator
from .entity import MonsterRemoteEntity
from .helpers import as_dict, retained, session_state, workout_active


@dataclass(frozen=True, kw_only=True)
class MonsterBinaryDescription(BinarySensorEntityDescription):
    """Describe a Monster Remote binary sensor."""

    value_fn: Callable[[dict[str, Any]], bool]


BINARY_SENSORS = (
    MonsterBinaryDescription(
        key="connected",
        name="Connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        value_fn=lambda data: bool(data.get("connected")),
    ),
    MonsterBinaryDescription(
        key="workout_active",
        name="Workout active",
        icon="mdi:weight-lifter",
        value_fn=workout_active,
    ),
    MonsterBinaryDescription(
        key="rest_active",
        name="Rest active",
        icon="mdi:timer-pause",
        value_fn=lambda data: bool(
            session_state(data).get("state") == "resting"
            or as_dict(retained(data).get("rest_state")).get("active")
        ),
    ),
    MonsterBinaryDescription(
        key="paused",
        name="Workout paused",
        icon="mdi:pause-circle",
        value_fn=lambda data: bool(
            session_state(data).get("paused")
            or as_dict(retained(data).get("playback_state")).get("paused")
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Monster Remote binary sensors."""
    coordinator: MonsterRemoteCoordinator = entry.runtime_data.coordinator
    async_add_entities(
        MonsterRemoteBinarySensor(coordinator, description)
        for description in BINARY_SENSORS
    )


class MonsterRemoteBinarySensor(MonsterRemoteEntity, BinarySensorEntity):
    """One Monster Remote binary sensor."""

    entity_description: MonsterBinaryDescription

    def __init__(
        self,
        coordinator: MonsterRemoteCoordinator,
        description: MonsterBinaryDescription,
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description
        self._attr_name = description.name

    @property
    def is_on(self) -> bool:
        """Return the binary state."""
        return self.entity_description.value_fn(self.coordinator.data or {})
