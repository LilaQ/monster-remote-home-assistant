"""Button platform for Monster Remote."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import MonsterRemoteCoordinator
from .entity import MonsterRemoteEntity


@dataclass(frozen=True, kw_only=True)
class MonsterButtonDescription(ButtonEntityDescription):
    """Describe a Monster Remote command button."""

    action: str


BUTTONS = (
    MonsterButtonDescription(
        key="weight_on", name="Weight on", icon="mdi:play", action="start-weight"
    ),
    MonsterButtonDescription(
        key="weight_off", name="Weight off", icon="mdi:stop", action="stop-weight"
    ),
    MonsterButtonDescription(
        key="increase_weight",
        name="Increase weight",
        icon="mdi:plus",
        action="increase-weight",
    ),
    MonsterButtonDescription(
        key="decrease_weight",
        name="Decrease weight",
        icon="mdi:minus",
        action="decrease-weight",
    ),
    MonsterButtonDescription(
        key="skip_set", name="Skip set", icon="mdi:skip-next", action="skip-set"
    ),
    MonsterButtonDescription(
        key="skip_exercise",
        name="Skip exercise",
        icon="mdi:skip-forward",
        action="skip-exercise",
    ),
    MonsterButtonDescription(
        key="skip_rest", name="Skip rest", icon="mdi:timer-skip", action="skip-rest"
    ),
    MonsterButtonDescription(
        key="increase_rest",
        name="Add 15 seconds rest",
        icon="mdi:timer-plus",
        action="increase-rest",
    ),
    MonsterButtonDescription(
        key="pause", name="Pause workout", icon="mdi:pause", action="pause"
    ),
    MonsterButtonDescription(
        key="resume", name="Resume workout", icon="mdi:play", action="resume"
    ),
    MonsterButtonDescription(
        key="flip_screen",
        name="Flip screen",
        icon="mdi:screen-rotation",
        action="flip-screen",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Monster Remote command buttons."""
    coordinator: MonsterRemoteCoordinator = entry.runtime_data.coordinator
    async_add_entities(
        MonsterRemoteButton(coordinator, description)
        for description in BUTTONS
    )


class MonsterRemoteButton(MonsterRemoteEntity, ButtonEntity):
    """One Monster Remote command button."""

    entity_description: MonsterButtonDescription

    def __init__(
        self,
        coordinator: MonsterRemoteCoordinator,
        description: MonsterButtonDescription,
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description
        self._attr_name = description.name

    async def async_press(self) -> None:
        """Run the mapped command."""
        await self.coordinator.async_command(self.entity_description.action)
