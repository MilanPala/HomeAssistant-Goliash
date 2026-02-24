"""Config flow for Goliash integration."""
from __future__ import annotations

import aiohttp
import voluptuous as vol

from homeassistant import config_entries

from .const import DOMAIN, CONF_USERNAME, CONF_PASSWORD, CONF_DEVICE_ID, API_LOGIN

STEP_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_DEVICE_ID): str,
    }
)


async def _validate_credentials(username: str, password: str) -> bool:
    """Validate credentials against the Goliash API."""
    async with aiohttp.ClientSession() as session:
        resp = await session.post(
            API_LOGIN,
            json={"username": username, "password": password},
        )
        return resp.status == 200


class GoliashConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Goliash."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            try:
                valid = await _validate_credentials(
                    user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
                )
                if valid:
                    await self.async_set_unique_id(user_input[CONF_DEVICE_ID])
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title=f"Goliash {user_input[CONF_DEVICE_ID]}",
                        data=user_input,
                    )
                else:
                    errors["base"] = "invalid_auth"
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_SCHEMA,
            errors=errors,
        )
