"""Coordinator for the DC Water integration."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import TYPE_CHECKING

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

try:
    from homeassistant.config_entries import ConfigEntryAuthFailed
except ImportError:  # pragma: no cover - compatibility fallback
    class ConfigEntryAuthFailed(Exception):
        """Fallback auth error for older Home Assistant versions."""

if TYPE_CHECKING:
    from pymydcwater import AccountInfo, DailyUsageRecord, DailyUsageReport


@dataclass(frozen=True)
class MyDCWaterSnapshot:
    """Latest coordinator snapshot."""

    account: AccountInfo
    report: DailyUsageReport
    latest_record: DailyUsageRecord
    requested_unit: str


class MyDCWaterCoordinator(DataUpdateCoordinator[MyDCWaterSnapshot]):
    """Manage periodic DC Water updates."""

    def __init__(
        self,
        hass,
        *,
        username: str,
        password: str,
        unit: str,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="DC Water",
            update_interval=UPDATE_INTERVAL,
        )
        from pymydcwater import MyDCWaterClient

        self._client = MyDCWaterClient(login=username, password=password)
        self.unit = unit

    async def _async_update_data(self) -> MyDCWaterSnapshot:
        """Fetch the latest reading from mydcwater."""
        from pymydcwater import AuthenticationError, MyDCWaterError

        try:
            return await self.hass.async_add_executor_job(self._fetch_data)
        except AuthenticationError as err:
            raise ConfigEntryAuthFailed("Authentication failed for mydcwater.") from err
        except MyDCWaterError as err:
            raise UpdateFailed(f"Unable to fetch mydcwater data: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected mydcwater update error: {err}") from err

    def _fetch_data(self) -> MyDCWaterSnapshot:
        months = self._client.get_available_months()
        if not months:
            raise RuntimeError("No billing months are available from mydcwater.")

        report = self._client.get_daily_usage(months[-1].key, unit=self.unit)
        if not report.records:
            raise RuntimeError("The latest billing month did not include any meter readings.")

        latest_record = report.records[-1]
        return MyDCWaterSnapshot(
            account=report.account,
            report=report,
            latest_record=latest_record,
            requested_unit=self.unit,
        )
