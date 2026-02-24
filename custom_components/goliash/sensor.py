"""Sensor platform for Goliash water meter."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
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
    """Sensor showing the current water meter reading."""

    has_entity_name = True
    translation_key = "water_meter"
    _attr_device_class = SensorDeviceClass.WATER
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = "m³"

    def __init__(self, coordinator: GoliashCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        device_id = entry.data[CONF_DEVICE_ID]
        self._attr_unique_id = f"goliash_{device_id}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=f"Goliash {device_id}",
            manufacturer="Goliash",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self):
        """Current water meter reading from API response."""
        try:
            return self.coordinator.data["graphData"]["currentState"]
        except (TypeError, KeyError):
            return None
