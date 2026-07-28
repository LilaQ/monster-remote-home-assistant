"""Base entity for Monster Remote."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MonsterRemoteCoordinator


class MonsterRemoteEntity(CoordinatorEntity[MonsterRemoteCoordinator]):
    """Common Monster Remote entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MonsterRemoteCoordinator,
        key: str,
    ) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"{coordinator.api.host}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.api.host)},
            manufacturer="Speediance",
            name="Gym Monster",
            model="Gym Monster with Monster Remote",
            sw_version=str(
                (coordinator.data or {})
                .get("health", {})
                .get("versionName", "")
            ),
            configuration_url=coordinator.api.base_url,
        )
