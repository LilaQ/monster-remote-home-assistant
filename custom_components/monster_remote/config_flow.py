"""Config flow for Monster Remote."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    MonsterRemoteAccessError,
    MonsterRemoteApi,
    MonsterRemoteAuthError,
    MonsterRemoteError,
)
from .const import CONF_SECRET, DEFAULT_PORT, DEFAULT_SECRET, DOMAIN


class MonsterRemoteConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Monster Remote config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Set up a Gym Monster."""
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            api = MonsterRemoteApi(
                async_get_clientsession(self.hass),
                host=host,
                port=user_input[CONF_PORT],
                secret=user_input[CONF_SECRET],
            )
            try:
                health = await api.health()
                await api.state()
            except MonsterRemoteAuthError:
                errors["base"] = "invalid_auth"
            except MonsterRemoteAccessError:
                errors["base"] = "premium_required"
            except MonsterRemoteError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(f"{host}:{user_input[CONF_PORT]}")
                self._abort_if_unique_id_configured(
                    updates={CONF_HOST: host}
                )
                title = health.get("service") or "Gym Monster"
                return self.async_create_entry(
                    title=str(title).replace("monster-helper", "Gym Monster"),
                    data={
                        CONF_HOST: host,
                        CONF_PORT: user_input[CONF_PORT],
                        CONF_SECRET: user_input[CONF_SECRET],
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Required(CONF_SECRET, default=DEFAULT_SECRET): str,
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
