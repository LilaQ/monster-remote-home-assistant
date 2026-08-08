"""Sensor platform for Monster Remote."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
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
    load_state,
    nested_value,
    resistance_event,
    retained,
    rounded,
    session_metrics,
    session_state,
    timestamp,
)


@dataclass(frozen=True, kw_only=True)
class MonsterSensorDescription(SensorEntityDescription):
    """Describe a Monster Remote sensor."""

    value_fn: Callable[[dict[str, Any]], Any]
    unit_fn: Callable[[dict[str, Any]], str | None] | None = None
    attributes_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None


def _progress(data):
    return as_dict(retained(data).get("course_exercise_progress"))


def _rowing(data):
    return as_dict(retained(data).get("live_rowing_metrics"))


def _weight(data):
    normalized = load_state(data)
    if normalized:
        return {
            "kg": normalized.get("weight"),
            "maxKg": normalized.get("maximum"),
        }
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


def _weight_unit(data: dict[str, Any]) -> str:
    unit = (
        load_state(data).get("unit")
        or retained(data).get("weight_unit")
        or (data.get("health") or {}).get("weightUnit")
    )
    return "lb" if unit == "lbs" else "kg"


def _health(data: dict[str, Any]) -> dict[str, Any]:
    value = data.get("health")
    return value if isinstance(value, dict) else {}


def _compatibility(data: dict[str, Any]) -> dict[str, Any]:
    health = _health(data)
    value = health.get("speedianceCompatibility")
    return value if isinstance(value, dict) else {}


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
        value_fn=lambda data: integer(
            session_state(data).get("exerciseIndex")
            or _progress(data).get("current")
        ),
    ),
    MonsterSensorDescription(
        key="exercise_total",
        name="Exercise total",
        icon="mdi:format-list-numbered",
        value_fn=lambda data: integer(
            session_state(data).get("exerciseTotal")
            or _progress(data).get("total")
        ),
    ),
    MonsterSensorDescription(
        key="set_index",
        name="Set",
        icon="mdi:counter",
        value_fn=lambda data: integer(
            session_state(data).get("setIndex")
        ) or (
            (integer(as_dict(retained(data).get("live_rep_index")).get("repIndex")) or 0) + 1
            if as_dict(retained(data).get("live_rep_index"))
            else None
        ),
    ),
    MonsterSensorDescription(
        key="current_reps",
        name="Current reps",
        icon="mdi:counter",
        value_fn=lambda data: integer(session_state(data).get("currentReps")),
    ),
    MonsterSensorDescription(
        key="target_reps",
        name="Target reps",
        icon="mdi:target",
        value_fn=lambda data: integer(session_state(data).get("targetReps")),
    ),
    MonsterSensorDescription(
        key="weight",
        name="Weight",
        icon="mdi:weight-kilogram",
        unit_fn=_weight_unit,
        value_fn=lambda data: rounded(_weight(data).get("kg")),
    ),
    MonsterSensorDescription(
        key="maximum_weight",
        name="Maximum weight",
        icon="mdi:weight-kilogram",
        unit_fn=_weight_unit,
        value_fn=lambda data: rounded(
            _weight(data).get("maxKg")
            or as_dict(retained(data).get("weight_capability")).get("max")
        ),
    ),
    MonsterSensorDescription(
        key="extra_weight",
        name="Extra weight",
        icon="mdi:weight-plus",
        unit_fn=_weight_unit,
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
        value_fn=lambda data: load_state(data).get("unit")
        or retained(data).get("weight_unit")
        or _health(data).get("weightUnit"),
    ),
    MonsterSensorDescription(
        key="accessories",
        name="Accessories",
        icon="mdi:dumbbell",
        value_fn=lambda data: nested_value(current_action(data), ("accessories",)),
    ),
    MonsterSensorDescription(
        key="session_status",
        name="Session status",
        icon="mdi:progress-clock",
        value_fn=lambda data: session_state(data).get("state") or "idle",
    ),
    MonsterSensorDescription(
        key="session_started",
        name="Session started",
        icon="mdi:clock-start",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: timestamp(session_state(data).get("startedAt")),
    ),
    MonsterSensorDescription(
        key="rest_started",
        name="Rest started",
        icon="mdi:timer-pause",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: timestamp(session_state(data).get("restStartedAt")),
    ),
    MonsterSensorDescription(
        key="session_reps",
        name="Session reps",
        icon="mdi:counter",
        value_fn=lambda data: integer(session_metrics(data).get("reps")),
    ),
    MonsterSensorDescription(
        key="session_sets",
        name="Session sets",
        icon="mdi:format-list-numbered",
        value_fn=lambda data: integer(session_metrics(data).get("sets")),
    ),
    MonsterSensorDescription(
        key="session_volume",
        name="Session volume",
        icon="mdi:weight",
        unit_fn=_weight_unit,
        value_fn=lambda data: rounded(session_metrics(data).get("volume")),
    ),
    MonsterSensorDescription(
        key="exercise_reps",
        name="Exercise reps",
        icon="mdi:counter",
        value_fn=lambda data: integer(session_metrics(data).get("exerciseReps")),
    ),
    MonsterSensorDescription(
        key="exercise_volume",
        name="Exercise volume",
        icon="mdi:weight",
        unit_fn=_weight_unit,
        value_fn=lambda data: rounded(session_metrics(data).get("exerciseVolume")),
    ),
    MonsterSensorDescription(
        key="rep_depth",
        name="Rep depth",
        icon="mdi:arrow-expand-vertical",
        native_unit_of_measurement="cm",
        value_fn=lambda data: rounded(
            session_metrics(data).get("repDepthCentimeters")
        ),
    ),
    MonsterSensorDescription(
        key="rep_side",
        name="Rep side",
        icon="mdi:swap-horizontal",
        value_fn=lambda data: session_metrics(data).get("repSide") or "unknown",
    ),
    MonsterSensorDescription(
        key="helper_version",
        name="Helper version",
        icon="mdi:package-variant-closed",
        value_fn=lambda data: _health(data).get("versionName"),
    ),
    MonsterSensorDescription(
        key="speediance_version",
        name="Speediance version",
        icon="mdi:information-outline",
        value_fn=lambda data: _compatibility(data).get("installedVersionName"),
    ),
    MonsterSensorDescription(
        key="profile_revision",
        name="Profile revision",
        icon="mdi:file-code-outline",
        value_fn=lambda data: integer(_compatibility(data).get("profileRevision")),
    ),
    MonsterSensorDescription(
        key="compatibility",
        name="Compatibility",
        icon="mdi:shield-check-outline",
        value_fn=lambda data: _compatibility(data).get("status"),
        attributes_fn=lambda data: {
            "reason": _compatibility(data).get("reason"),
            "build_id": _compatibility(data).get("installedBuildId"),
            "profile_source": _compatibility(data).get("profileSource"),
            "supported_versions": _compatibility(data).get("supportedVersions", []),
        },
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

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the live device unit where the entity is unit-aware."""
        unit_fn = self.entity_description.unit_fn
        if unit_fn is not None:
            return unit_fn(self.coordinator.data or {})
        return self.entity_description.native_unit_of_measurement

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return compact diagnostics without creating duplicate entities."""
        attributes_fn = self.entity_description.attributes_fn
        if attributes_fn is None:
            return None
        return {
            key: value
            for key, value in attributes_fn(self.coordinator.data or {}).items()
            if value is not None
        }
