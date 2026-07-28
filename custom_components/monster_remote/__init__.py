"""Monster Remote Home Assistant integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MonsterRemoteApi
from .const import PLATFORMS
from .coordinator import MonsterRemoteCoordinator


@dataclass(slots=True)
class MonsterRemoteRuntimeData:
    """Runtime data stored on the config entry."""

    api: MonsterRemoteApi
    coordinator: MonsterRemoteCoordinator


MonsterRemoteConfigEntry = ConfigEntry[MonsterRemoteRuntimeData]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MonsterRemoteConfigEntry,
) -> bool:
    """Set up Monster Remote from a config entry."""
    api = MonsterRemoteApi(
        async_get_clientsession(hass),
        host=entry.data["host"],
        port=entry.data["port"],
    )
    coordinator = MonsterRemoteCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = MonsterRemoteRuntimeData(api, coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    coordinator.start_event_stream()
    return True


async def async_migrate_entry(
    hass: HomeAssistant,
    entry: MonsterRemoteConfigEntry,
) -> bool:
    """Remove legacy setup fields that are now internal."""
    if entry.version < 2:
        data = dict(entry.data)
        data.pop("secret", None)
        hass.config_entries.async_update_entry(
            entry,
            data=data,
            version=2,
        )
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: MonsterRemoteConfigEntry,
) -> bool:
    """Unload a Monster Remote config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.coordinator.stop_event_stream()
    return unloaded
