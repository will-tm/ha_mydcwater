"""Pure helpers for the DC Water integration."""

from __future__ import annotations

WATER_DEVICE_CLASS_UNITS = {"CuFt", "Gal"}
VOLUME_UNIT_MAP = {
    "CuFt": "ft³",
    "CCF": "CCF",
    "Gal": "gal",
}


def native_volume_unit(unit_key: str) -> str:
    """Map a mydcwater unit key to the Home Assistant sensor unit string."""
    return VOLUME_UNIT_MAP.get(unit_key, unit_key)


def supports_water_device_class(unit_key: str) -> bool:
    """Return whether the unit can be exposed as a water device class."""
    return unit_key in WATER_DEVICE_CLASS_UNITS
