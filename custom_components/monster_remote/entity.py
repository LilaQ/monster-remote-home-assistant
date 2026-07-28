"""Base entity for Monster Remote."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MonsterRemoteCoordinator


class MonsterRemoteEntity(CoordinatorEntity[MonsterRemoteCoordinator]):
    """Common Monster Remote entity."""

    # Keep concise entity/button names such as "Weight on". Home Assistant
    # otherwise prepends the device name to every single entity.
    _attr_has_entity_name = False

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
            name="Monster Remote",
            model="Monster Remote",
            sw_version=str(
                (coordinator.data or {})
                .get("health", {})
                .get("versionName", "")
            ),
            configuration_url=coordinator.api.base_url,
        )
