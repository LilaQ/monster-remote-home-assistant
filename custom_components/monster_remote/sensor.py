"""Sensor platform for Monster Remote."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import MonsterRemoteCoordinator
from .entity import MonsterRemoteEntity
from .helpers import (
    as_dict,
    current_action,
    current_screen,
    exercise_name,
    integer,
    nested_value,
    resistance_event,
    retained,
    rounded,
)


@dataclass(frozen=True, kw_only=True)
class MonsterSensorDescription(SensorEntityDescription):
    """Describe a Monster Remote sensor."""

    value_fn: Callable[[dict[str, Any]], Any]


def _progress(data):
    return as_dict(retained(data).get("course_exercise_progress"))


def _rowing(data):
    return as_dict(retained(data).get("live_rowing_metrics"))


def _weight(data):
    state = retained(data)
    snapshot = as_dict(state.get("live_resistance_kg"))
    event = as_dict(state.get("live_resistance"))
    if event.get("kind") in ("mainKg", "speedKg"):
        snapshot = dict(snapshot)
        if event.get("value") is not None:
            snapshot["kg"] = event["value"]
        if event.get("max") is not None:
            snapshot["maxKg"] = event["max"]
    return snapshot


SENSORS = (
    MonsterSensorDescription(
        key="screen",
        name="Screen",
        icon="mdi:monitor-dashboard",
        value_fn=current_screen,
    ),
    MonsterSensorDescription(
        key="exercise",
        name="Exercise",
        icon="mdi:weight-lifter",
        value_fn=exercise_name,
    ),
    MonsterSensorDescription(
        key="exercise_index",
        name="Exercise index",
        icon="mdi:format-list-numbered",
        value_fn=lambda data: integer(_progress(data).get("current")),
    ),
    MonsterSensorDescription(
        key="exercise_total",
        name="Exercise total",
        icon="mdi:format-list-numbered",
        value_fn=lambda data: integer(_progress(data).get("total")),
    ),
    MonsterSensorDescription(
        key="set_index",
        name="Set",
        icon="mdi:counter",
        value_fn=lambda data: (
            (integer(as_dict(retained(data).get("live_rep_index")).get("repIndex")) or 0) + 1
            if as_dict(retained(data).get("live_rep_index"))
            else None
        ),
    ),
    MonsterSensorDescription(
        key="weight",
        name="Weight",
        icon="mdi:weight-kilogram",
        native_unit_of_measurement="kg",
        value_fn=lambda data: rounded(_weight(data).get("kg")),
    ),
    MonsterSensorDescription(
        key="maximum_weight",
        name="Maximum weight",
        icon="mdi:weight-kilogram",
        native_unit_of_measurement="kg",
        value_fn=lambda data: rounded(
            _weight(data).get("maxKg")
            or as_dict(retained(data).get("weight_capability")).get("max")
        ),
    ),
    MonsterSensorDescription(
        key="extra_weight",
        name="Extra weight",
        icon="mdi:weight-plus",
        native_unit_of_measurement="kg",
        value_fn=lambda data: rounded(resistance_event(data, "extraKg").get("value")),
    ),
    MonsterSensorDescription(
        key="resistance",
        name="Resistance",
        icon="mdi:tune-vertical",
        value_fn=lambda data: rounded(
            _rowing(data).get("resistance")
            or resistance_event(data, "cardioLevel").get("value"),
            0,
        ),
    ),
    MonsterSensorDescription(
        key="heart_rate",
        name="Heart rate",
        icon="mdi:heart-pulse",
        native_unit_of_measurement="bpm",
        value_fn=lambda data: integer(
            as_dict(retained(data).get("live_heart_rate")).get("heartRate")
        ),
    ),
    MonsterSensorDescription(
        key="rowing_speed",
        name="Rowing speed",
        icon="mdi:speedometer",
        native_unit_of_measurement="km/h",
        value_fn=lambda data: rounded(_rowing(data).get("speedKmh")),
    ),
    MonsterSensorDescription(
        key="rowing_power",
        name="Rowing power",
        icon="mdi:flash",
        native_unit_of_measurement="W",
        value_fn=lambda data: rounded(_rowing(data).get("powerW"), 0),
    ),
    MonsterSensorDescription(
        key="rowing_distance",
        name="Rowing distance",
        icon="mdi:map-marker-distance",
        native_unit_of_measurement="m",
        value_fn=lambda data: rounded(_rowing(data).get("distanceM"), 0),
    ),
    MonsterSensorDescription(
        key="rowing_spm",
        name="Rowing stroke rate",
        icon="mdi:rowing",
        native_unit_of_measurement="spm",
        value_fn=lambda data: rounded(_rowing(data).get("spm"), 0),
    ),
    MonsterSensorDescription(
        key="weight_unit",
        name="Weight unit",
        icon="mdi:ruler",
        value_fn=lambda data: retained(data).get("weight_unit")
        or (data.get("health") or {}).get("weightUnit"),
    ),
    MonsterSensorDescription(
        key="accessories",
        name="Accessories",
        icon="mdi:dumbbell",
        value_fn=lambda data: nested_value(current_action(data), ("accessories",)),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Monster Remote sensors."""
    coordinator: MonsterRemoteCoordinator = entry.runtime_data.coordinator
    async_add_entities(
        MonsterRemoteSensor(coordinator, description)
        for description in SENSORS
    )


class MonsterRemoteSensor(MonsterRemoteEntity, SensorEntity):
    """One Monster Remote sensor."""

    entity_description: MonsterSensorDescription

    def __init__(
        self,
        coordinator: MonsterRemoteCoordinator,
        description: MonsterSensorDescription,
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description
        self._attr_name = description.name

    @property
    def native_value(self):
        """Return the current sensor value."""
        return self.entity_description.value_fn(self.coordinator.data or {})
