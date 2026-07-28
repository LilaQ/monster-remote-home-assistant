"""Number platform for Monster Remote."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import MonsterRemoteCoordinator
from .entity import MonsterRemoteEntity
from .helpers import as_dict, resistance_event, retained, rounded


@dataclass(frozen=True, kw_only=True)
class MonsterNumberDescription(NumberEntityDescription):
    """Describe a Monster Remote target number."""

    action: str
    argument: str


NUMBERS = (
    MonsterNumberDescription(
        key="target_weight",
        name="Target weight",
        icon="mdi:weight-kilogram",
        native_min_value=0.5,
        native_max_value=100.0,
        native_step=0.5,
        native_unit_of_measurement="kg",
        mode=NumberMode.BOX,
        action="set-weight",
        argument="kg",
    ),
    MonsterNumberDescription(
        key="target_extra_weight",
        name="Target extra weight",
        icon="mdi:weight-plus",
        native_min_value=0.0,
        native_max_value=100.0,
        native_step=0.5,
        native_unit_of_measurement="kg",
        mode=NumberMode.BOX,
        action="set-extra-weight",
        argument="extraKg",
    ),
    MonsterNumberDescription(
        key="target_resistance",
        name="Target resistance",
        icon="mdi:tune-vertical",
        native_min_value=1,
        native_max_value=25,
        native_step=1,
        mode=NumberMode.SLIDER,
        action="set-resistance",
        argument="resistance",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Monster Remote numbers."""
    coordinator: MonsterRemoteCoordinator = entry.runtime_data.coordinator
    async_add_entities(
        MonsterRemoteNumber(coordinator, description)
        for description in NUMBERS
    )


class MonsterRemoteNumber(MonsterRemoteEntity, NumberEntity):
    """One Monster Remote target number."""

    entity_description: MonsterNumberDescription

    def __init__(
        self,
        coordinator: MonsterRemoteCoordinator,
        description: MonsterNumberDescription,
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description
        self._attr_name = description.name

    @property
    def native_value(self):
        """Return the current matching value."""
        state = retained(self.coordinator.data or {})
        if self.entity_description.key == "target_weight":
            return rounded(as_dict(state.get("live_resistance_kg")).get("kg"))
        if self.entity_description.key == "target_extra_weight":
            return rounded(resistance_event(self.coordinator.data or {}, "extraKg").get("value"))
        rowing = as_dict(state.get("live_rowing_metrics"))
        return rounded(
            rowing.get("resistance")
            or resistance_event(self.coordinator.data or {}, "cardioLevel").get("value"),
            0,
        )

    @property
    def native_max_value(self) -> float:
        """Use the live machine capability where available."""
        if self.entity_description.key != "target_weight":
            return float(self.entity_description.native_max_value)
        state = retained(self.coordinator.data or {})
        capability = as_dict(state.get("weight_capability"))
        resistance = as_dict(state.get("live_resistance_kg"))
        value = capability.get("max") or resistance.get("maxKg")
        return float(value) if isinstance(value, (int, float)) and value > 0 else 100.0

    async def async_set_native_value(self, value: float) -> None:
        """Set the target value."""
        await self.coordinator.async_command(
            self.entity_description.action,
            **{self.entity_description.argument: value},
        )
