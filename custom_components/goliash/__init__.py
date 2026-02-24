"""Goliash custom integration."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_DEVICE_ID,
    API_LOGIN,
    API_MEASUREMENTS,
)

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[Platform] = [Platform.SENSOR]
SCAN_INTERVAL = timedelta(hours=12)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Goliash from a config entry."""
    coordinator = GoliashCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


class GoliashCoordinator(DataUpdateCoordinator):
    """Coordinator for fetching data from Goliash API."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)
        self._username = entry.data[CONF_USERNAME]
        self._password = entry.data[CONF_PASSWORD]
        self._device_id = entry.data[CONF_DEVICE_ID]
        self._token: str | None = None

    async def _login(self) -> str:
        """Authenticate and return a JWT token."""
        async with aiohttp.ClientSession() as session:
            resp = await session.post(
                API_LOGIN,
                json={"username": self._username, "password": self._password},
            )
            resp.raise_for_status()
            data = await resp.json()
            return data["token"]

    async def _async_update_data(self) -> dict:
        """Fetch current water meter state."""
        try:
            self._token = await self._login()

            now = datetime.now(timezone.utc)
            date_from = (now - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
            date_to = now.strftime("%Y-%m-%dT%H:%M:%S.000Z")

            url = API_MEASUREMENTS.format(device_id=self._device_id)
            async with aiohttp.ClientSession() as session:
                resp = await session.post(
                    url,
                    headers={"Authorization": f"Bearer {self._token}"},
                    json={"dateFrom": date_from, "dateTo": date_to, "type": "consumption"},
                )
                resp.raise_for_status()
                return await resp.json()

        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with Goliash API: {err}") from err
        except KeyError as err:
            raise UpdateFailed(f"Unexpected API response structure: {err}") from err
