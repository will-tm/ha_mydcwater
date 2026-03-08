"""Constants for the DC Water integration."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.const import Platform

DOMAIN = "mydcwater"
MANUFACTURER = "DC Water"

CONF_UNIT = "unit"
DEFAULT_UNIT = "CuFt"
SUPPORTED_UNITS: tuple[str, ...] = ("CuFt", "CCF", "Gal")

PLATFORMS: list[Platform] = [Platform.SENSOR]
UPDATE_INTERVAL = timedelta(hours=1)

ATTR_ACCOUNT_NAME = "account_name"
ATTR_ACCOUNT_NUMBER = "account_number"
ATTR_SERVICE_ADDRESS = "service_address"
ATTR_READING_TIME = "reading_time"
ATTR_PORT1_USAGE = "port1_usage"
ATTR_PORT2_USAGE = "port2_usage"
ATTR_PORTAL_UNIT = "portal_unit"
