"""Async local HTTP client for Monster Helper."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass
import json
from typing import Any
from urllib.parse import urlencode

import aiohttp

_HELPER_SECRET = "lilaq-monster-9f3a2c7e1b"


class MonsterRemoteError(Exception):
    """Base API error."""


class MonsterRemoteAuthError(MonsterRemoteError):
    """Authentication failed."""


class MonsterRemoteAccessError(MonsterRemoteError):
    """Premium/trial access is unavailable."""


@dataclass(slots=True, frozen=True)
class MonsterRemoteEvent:
    """One event from Monster Helper."""

    event: str
    data: dict[str, Any]


class MonsterRemoteApi:
    """Client for the local Monster Helper API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int,
    ) -> None:
        self._session = session
        self.host = host.strip().removeprefix("http://").removeprefix("https://").rstrip("/")
        self.port = port

    @property
    def base_url(self) -> str:
        """Return the Helper base URL."""
        return f"http://{self.host}:{self.port}"

    @property
    def headers(self) -> dict[str, str]:
        """Return authenticated request headers."""
        return {"X-Monster-Secret": _HELPER_SECRET}

    async def health(self) -> dict[str, Any]:
        """Fetch public health information."""
        return await self._get_json("/health", authenticated=False)

    async def state(self) -> dict[str, Any]:
        """Fetch the retained Monster Remote state."""
        return await self._get_json("/state")

    async def start_mirror(self) -> dict[str, Any]:
        """Start the Helper's local H.264 mirror source."""
        return await self._get_json("/mirror/start")

    @property
    def mirror_stream_url(self) -> str:
        """Return an authenticated elementary H.264 stream URL."""
        return f"{self.base_url}/mirror/stream?secret={_HELPER_SECRET}"

    async def command(
        self,
        action: str,
        *,
        view: str = "auto",
        **arguments: str | int | float,
    ) -> dict[str, Any]:
        """Run one native Monster Remote command."""
        params: dict[str, str | int | float] = {
            "action": action,
            "view": view,
            **arguments,
        }
        return await self._get_json("/command", params=params)

    async def events(self) -> AsyncIterator[MonsterRemoteEvent]:
        """Yield snapshot/update events from the authenticated SSE stream."""
        timeout = aiohttp.ClientTimeout(total=None, connect=5, sock_read=45)
        try:
            async with self._session.get(
                f"{self.base_url}/events",
                headers=self.headers,
                timeout=timeout,
            ) as response:
                await self._raise_for_status(response)
                event_name = "message"
                data_lines: list[str] = []
                async for raw_line in response.content:
                    line = raw_line.decode(
                        "utf-8", errors="replace"
                    ).rstrip("\r\n")
                    if not line:
                        if data_lines:
                            raw_data = "\n".join(data_lines)
                            try:
                                payload = json.loads(raw_data)
                            except json.JSONDecodeError:
                                payload = {"raw": raw_data}
                            if isinstance(payload, dict):
                                yield MonsterRemoteEvent(event_name, payload)
                        event_name = "message"
                        data_lines.clear()
                        continue
                    if line.startswith(":"):
                        continue
                    field, _, value = line.partition(":")
                    value = value.lstrip()
                    if field == "event":
                        event_name = value
                    elif field == "data":
                        data_lines.append(value)
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise MonsterRemoteError(str(err)) from err

    async def _get_json(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        authenticated: bool = True,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        if params:
            url = f"{url}?{urlencode(params)}"
        timeout = aiohttp.ClientTimeout(total=6)
        try:
            async with self._session.get(
                url,
                headers=self.headers if authenticated else None,
                timeout=timeout,
            ) as response:
                await self._raise_for_status(response)
                payload = await response.json(content_type=None)
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise MonsterRemoteError(str(err)) from err
        if not isinstance(payload, dict):
            raise MonsterRemoteError("Helper returned an invalid response")
        if payload.get("ok") is False:
            error = str(payload.get("error", "command_failed"))
            if error == "trial_expired":
                raise MonsterRemoteAccessError(error)
            raise MonsterRemoteError(error)
        return payload

    async def _raise_for_status(self, response: aiohttp.ClientResponse) -> None:
        if response.status == 401:
            raise MonsterRemoteAuthError("invalid_secret")
        if response.status == 403:
            raise MonsterRemoteAccessError("premium_required")
        if response.status >= 400:
            body = await response.text()
            raise MonsterRemoteError(f"HTTP {response.status}: {body[:200]}")
