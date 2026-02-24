"""Senzor entity pro Goliash vodoměr."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_DEVICE_ID
from . import GoliashCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: GoliashCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([GoliashWaterSensor(coordinator, entry)])


class GoliashWaterSensor(CoordinatorEntity, SensorEntity):
    """Senzor zobrazující aktuální stav vodoměru."""

    _attr_device_class = SensorDeviceClass.WATER
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = "m³"
    _attr_icon = "mdi:water"

    def __init__(self, coordinator: GoliashCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._device_id = entry.data[CONF_DEVICE_ID]
        self._attr_unique_id = f"goliash_{self._device_id}"
        self._attr_name = f"Vodoměr {self._device_id}"

    @property
    def native_value(self):
        """Aktuální stav vodoměru z API odpovědi."""
        try:
            return self.coordinator.data["device"]["graphData"]["currentState"]
        except (TypeError, KeyError):
            return None
