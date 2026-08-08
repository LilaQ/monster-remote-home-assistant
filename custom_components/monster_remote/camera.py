"""Live Gym Monster display camera."""

from __future__ import annotations

from homeassistant.components.camera import Camera

from . import MonsterRemoteConfigEntry
from .entity import MonsterRemoteEntity


async def async_setup_entry(hass, entry: MonsterRemoteConfigEntry, async_add_entities) -> None:
    """Set up the on-demand local H.264 mirror camera."""
    async_add_entities([MonsterRemoteMirrorCamera(entry.runtime_data.coordinator)])


class MonsterRemoteMirrorCamera(MonsterRemoteEntity, Camera):
    """Camera backed by the Helper's on-demand scrcpy H.264 stream."""

    _attr_name = "Gym Monster display"
    _attr_is_streaming = True

    def __init__(self, coordinator) -> None:
        Camera.__init__(self)
        MonsterRemoteEntity.__init__(self, coordinator, "display_camera")

    async def async_stream_source(self) -> str | None:
        """Start capture and return the authenticated local stream URL."""
        await self.coordinator.api.start_mirror()
        return self.coordinator.api.mirror_stream_url

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Home Assistant obtains frames from the stream source."""
        return None
