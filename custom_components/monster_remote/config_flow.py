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
from .const import DEFAULT_PORT, DOMAIN


class MonsterRemoteConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Monster Remote config flow."""

    VERSION = 2

    async def async_step_user(self, user_input=None):
        """Set up Monster Remote."""
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            api = MonsterRemoteApi(
                async_get_clientsession(self.hass),
                host=host,
                port=user_input[CONF_PORT],
            )
            try:
                await api.health()
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
                return self.async_create_entry(
                    title="Monster Remote",
                    data={
                        CONF_HOST: host,
                        CONF_PORT: user_input[CONF_PORT],
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
