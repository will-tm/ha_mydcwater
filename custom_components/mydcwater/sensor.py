"""Sensor platform for the DC Water integration."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_ACCOUNT_NAME,
    ATTR_ACCOUNT_NUMBER,
    ATTR_PORT1_USAGE,
    ATTR_PORT2_USAGE,
    ATTR_PORTAL_UNIT,
    ATTR_READING_TIME,
    ATTR_SERVICE_ADDRESS,
    DOMAIN,
    MANUFACTURER,
)
from .coordinator import MyDCWaterCoordinator, MyDCWaterSnapshot
from .helpers import native_volume_unit, supports_water_device_class


@dataclass(frozen=True, kw_only=True)
class MyDCWaterSensorEntityDescription(SensorEntityDescription):
    """DC Water sensor description."""

    value_fn: Callable[[MyDCWaterSnapshot], Any]
    attribute_fn: Callable[[MyDCWaterSnapshot], Mapping[str, Any]] | None = None
    volume_sensor: bool = False


def _usage_attributes(data: MyDCWaterSnapshot) -> Mapping[str, Any]:
    return {
        ATTR_ACCOUNT_NAME: data.account.account_name,
        ATTR_ACCOUNT_NUMBER: data.account.account_number,
        ATTR_SERVICE_ADDRESS: data.account.service_address,
        ATTR_READING_TIME: data.latest_record.reading_time,
        ATTR_PORT1_USAGE: data.latest_record.port1_usage,
        ATTR_PORT2_USAGE: data.latest_record.port2_usage,
        ATTR_PORTAL_UNIT: data.requested_unit,
    }


SENSORS: tuple[MyDCWaterSensorEntityDescription, ...] = (
    MyDCWaterSensorEntityDescription(
        key="latest_meter_reading",
        translation_key="latest_meter_reading",
        icon="mdi:counter",
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=2,
        value_fn=lambda data: data.latest_record.reading_value,
        attribute_fn=_usage_attributes,
        volume_sensor=True,
    ),
    MyDCWaterSensorEntityDescription(
        key="latest_daily_usage",
        translation_key="latest_daily_usage",
        icon="mdi:water",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda data: data.latest_record.usage,
        attribute_fn=_usage_attributes,
        volume_sensor=True,
    ),
    MyDCWaterSensorEntityDescription(
        key="daily_average",
        translation_key="daily_average",
        icon="mdi:chart-line",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda data: data.report.daily_average,
        attribute_fn=_usage_attributes,
        volume_sensor=True,
    ),
    MyDCWaterSensorEntityDescription(
        key="annual_average",
        translation_key="annual_average",
        icon="mdi:chart-bell-curve-cumulative",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda data: data.report.annual_average,
        attribute_fn=_usage_attributes,
        volume_sensor=True,
    ),
    MyDCWaterSensorEntityDescription(
        key="latest_reading_timestamp",
        translation_key="latest_reading_timestamp",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.latest_record.reading_datetime,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up DC Water sensors based on a config entry."""
    coordinator: MyDCWaterCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(MyDCWaterSensor(coordinator, entry, description) for description in SENSORS)


class MyDCWaterSensor(CoordinatorEntity[MyDCWaterCoordinator], SensorEntity):
    """Representation of a DC Water sensor."""

    entity_description: MyDCWaterSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MyDCWaterCoordinator,
        entry: ConfigEntry,
        description: MyDCWaterSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_translation_key = description.translation_key

    @property
    def device_info(self) -> DeviceInfo:
        """Return device metadata for the account."""
        data = self.coordinator.data
        identifiers = {(DOMAIN, self._entry.unique_id or self._entry.entry_id)}
        return DeviceInfo(
            identifiers=identifiers,
            manufacturer=MANUFACTURER,
            name=self._entry.title,
            model="Water Meter",
            serial_number=data.account.account_number,
        )

    @property
    def native_value(self) -> Any:
        """Return the current entity state."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement."""
        if not self.entity_description.volume_sensor:
            return self.entity_description.native_unit_of_measurement
        return native_volume_unit(self.coordinator.data.requested_unit)

    @property
    def device_class(self) -> SensorDeviceClass | None:
        """Return the device class."""
        if not self.entity_description.volume_sensor:
            return self.entity_description.device_class
        if supports_water_device_class(self.coordinator.data.requested_unit):
            return SensorDeviceClass.WATER
        return None

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return additional attributes for the sensor."""
        if self.entity_description.attribute_fn is None:
            return None
        return self.entity_description.attribute_fn(self.coordinator.data)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated coordinator data."""
        self.async_write_ha_state()
