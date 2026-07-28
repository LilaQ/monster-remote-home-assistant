"""Push coordinator for Monster Remote."""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from typing import Any

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    MonsterRemoteAccessError,
    MonsterRemoteApi,
    MonsterRemoteAuthError,
    MonsterRemoteError,
)
from .const import DOMAIN, EVENT_MONSTER_REMOTE

_LOGGER = logging.getLogger(__name__)


class MonsterRemoteCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate retained state, push events and fallback polling."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api: MonsterRemoteApi,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=10),
            always_update=False,
        )
        self.api = api
        self._event_task: asyncio.Task[None] | None = None

    async def _async_update_data(self) -> dict[str, Any]:
        """Refresh the full retained snapshot as a reconnect fallback."""
        try:
            health, snapshot = await asyncio.gather(
                self.api.health(),
                self.api.state(),
            )
        except MonsterRemoteAuthError as err:
            raise UpdateFailed("Monster Helper authentication failed") from err
        except MonsterRemoteAccessError as err:
            raise UpdateFailed("Monster Remote Premium is required") from err
        except MonsterRemoteError as err:
            raise UpdateFailed(f"Unable to reach Monster Helper: {err}") from err
        return {
            "health": health,
            "state": snapshot.get("state", {}),
            "connected": bool(snapshot.get("connected")),
            "last_event_at": snapshot.get("lastEventAt"),
        }

    def start_event_stream(self) -> None:
        """Start the SSE reconnect loop."""
        if self._event_task is None or self._event_task.done():
            self._event_task = self.hass.async_create_background_task(
                self._event_loop(),
                "Monster Remote events",
            )

    async def stop_event_stream(self) -> None:
        """Stop the SSE reconnect loop."""
        if self._event_task is None:
            return
        self._event_task.cancel()
        try:
            await self._event_task
        except asyncio.CancelledError:
            pass
        self._event_task = None

    async def async_command(
        self,
        action: str,
        *,
        view: str = "auto",
        **arguments: str | int | float,
    ) -> dict[str, Any]:
        """Run a command and refresh retained state without delaying success."""
        result = await self.api.command(action, view=view, **arguments)
        # Commands return after the native operation has completed and its
        # retained snapshot has been published. Refresh immediately as a
        # deterministic fallback in case the SSE frame is delayed by Wi-Fi.
        # A refresh failure must not turn an already successful command into
        # a failed Home Assistant button action.
        self.hass.async_create_background_task(
            self._refresh_after_command(),
            f"Monster Remote refresh after {action}",
        )
        return result

    async def _refresh_after_command(self) -> None:
        try:
            await self.async_request_refresh()
        except asyncio.CancelledError:
            raise
        except Exception as err:  # Home Assistant coordinator owns specifics
            _LOGGER.debug("Post-command state refresh failed: %s", err)

    async def _event_loop(self) -> None:
        delay = 1
        while True:
            try:
                async for event in self.api.events():
                    delay = 1
                    if event.event == "snapshot":
                        self._apply_snapshot(event.data)
                    elif event.event == "update":
                        self._apply_update(event.data)
            except asyncio.CancelledError:
                raise
            except (
                MonsterRemoteError,
                aiohttp.ClientError,
                OSError,
                asyncio.TimeoutError,
            ) as err:
                _LOGGER.debug("Monster Remote event stream reconnect: %s", err)
                # The connectivity entity describes the Helper/device, not the
                # optional SSE transport. Older Helper builds do not expose
                # /events and transient Wi-Fi reconnects can also rebuild the
                # stream while /health and /state remain fully reachable.
                # Keep the last REST-derived connectivity state here; the
                # coordinator poll is authoritative for actual disconnects.
            await asyncio.sleep(delay)
            delay = min(delay * 2, 30)

    def _apply_snapshot(self, payload: dict[str, Any]) -> None:
        current = dict(self.data or {})
        current["state"] = payload.get("state", {})
        current["connected"] = bool(payload.get("connected"))
        current["last_event_at"] = payload.get("lastEventAt")
        self.async_set_updated_data(current)

    def _apply_update(self, payload: dict[str, Any]) -> None:
        key = payload.get("key")
        if not isinstance(key, str) or not key:
            return
        current = dict(self.data or {})
        state = dict(current.get("state", {}))
        state[key] = payload.get("value")
        current["state"] = state
        current["connected"] = True
        current["last_event_at"] = payload.get("timestamp")
        self.async_set_updated_data(current)
        self.hass.bus.async_fire(
            EVENT_MONSTER_REMOTE,
            {
                "key": key,
                "value": payload.get("value"),
                "timestamp": payload.get("timestamp"),
                "sequence": payload.get("sequence"),
                "host": self.api.host,
                "config_entry_id": self.config_entry.entry_id,
            },
        )
