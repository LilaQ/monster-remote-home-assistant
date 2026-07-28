"""Select platform for Monster Remote."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import MonsterRemoteCoordinator
from .entity import MonsterRemoteEntity
from .helpers import as_dict, load_state, retained


@dataclass(frozen=True, kw_only=True)
class MonsterSelectDescription(SelectEntityDescription):
    """Describe a Monster Remote select."""

    action: str
    argument: str


SELECTS = (
    MonsterSelectDescription(
        key="mode",
        name="Training mode",
        icon="mdi:weight-lifter",
        options=[
            "standard",
            "chain",
            "eccentric",
            "constant-speed",
            "rowing",
            "skiing",
            "pilates",
        ],
        action="set-mode",
        argument="mode",
    ),
    MonsterSelectDescription(
        key="device",
        name="Load setup",
        icon="mdi:dumbbell",
        options=["non-barbell", "barbell", "dual-load"],
        action="set-device",
        argument="device",
    ),
    MonsterSelectDescription(
        key="spotter",
        name="Spotter mode",
        icon="mdi:shield-account",
        options=["off", "1", "2"],
        action="set-spotter",
        argument="spotter",
    ),
    MonsterSelectDescription(
        key="resistance_mode",
        name="Resistance mode",
        icon="mdi:auto-mode",
        options=["auto", "manual"],
        action="resistance-mode",
        argument="mode",
    ),
)

MODE_BY_VALUE = {
    1: "standard",
    2: "chain",
    3: "eccentric",
    4: "constant-speed",
    5: "rowing",
    6: "skiing",
    8: "pilates",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Monster Remote selects."""
    coordinator: MonsterRemoteCoordinator = entry.runtime_data.coordinator
    async_add_entities(
        MonsterRemoteSelect(coordinator, description)
        for description in SELECTS
    )


class MonsterRemoteSelect(MonsterRemoteEntity, SelectEntity):
    """One Monster Remote select."""

    entity_description: MonsterSelectDescription

    def __init__(
        self,
        coordinator: MonsterRemoteCoordinator,
        description: MonsterSelectDescription,
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description
        self._attr_name = description.name
        self._selected: str | None = None

    @property
    def current_option(self) -> str | None:
        """Return the retained or last selected option."""
        state = retained(self.coordinator.data or {})
        if self.entity_description.key == "mode":
            mode = (
                load_state(self.coordinator.data or {}).get("mode")
                or as_dict(state.get("live_resistance")).get("mode")
            )
            if isinstance(mode, (int, float)):
                return MODE_BY_VALUE.get(int(mode), self._selected)
        elif self.entity_description.key == "device":
            device = (
                load_state(self.coordinator.data or {}).get("device")
                or as_dict(state.get("weight_capability")).get("device")
            )
            mapped = {
                "single": "non-barbell",
                "barbell": "barbell",
            }.get(device)
            return mapped or self._selected
        return self._selected

    async def async_select_option(self, option: str) -> None:
        """Select an option."""
        if self.entity_description.key == "resistance_mode":
            action = (
                "resistance-auto"
                if option == "auto"
                else "resistance-manual"
            )
            await self.coordinator.async_command(action)
        else:
            await self.coordinator.async_command(
                self.entity_description.action,
                **{self.entity_description.argument: option},
            )
        self._selected = option
        self.async_write_ha_state()
