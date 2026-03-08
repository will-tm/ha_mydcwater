"""Config flow for the DC Water integration."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

import voluptuous as vol

from pymydcwater import AuthenticationError, MyDCWaterClient, MyDCWaterError

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlowWithConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_UNIT, DEFAULT_UNIT, DOMAIN, SUPPORTED_UNITS

_LOGGER = logging.getLogger(__name__)


class CannotConnect(Exception):
    """Error to indicate the portal is unavailable."""


class InvalidAuth(Exception):
    """Error to indicate the credentials are invalid."""


@dataclass(frozen=True)
class ValidationResult:
    """Validated config-entry details."""

    title: str
    unique_id: str


def _build_user_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_USERNAME, default=defaults.get(CONF_USERNAME, "")): str,
            vol.Required(CONF_PASSWORD, default=defaults.get(CONF_PASSWORD, "")): str,
            vol.Required(CONF_UNIT, default=defaults.get(CONF_UNIT, DEFAULT_UNIT)): vol.In(
                SUPPORTED_UNITS
            ),
        }
    )


def _build_options_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_UNIT, default=defaults.get(CONF_UNIT, DEFAULT_UNIT)): vol.In(
                SUPPORTED_UNITS
            ),
        }
    )


def _validate_credentials(data: dict[str, Any]) -> ValidationResult:
    client = MyDCWaterClient(login=data[CONF_USERNAME], password=data[CONF_PASSWORD])
    try:
        available_months = client.get_available_months()
        if not available_months:
            raise CannotConnect("No daily usage months were returned.")
        report = client.get_daily_usage(available_months[-1].key, unit=data[CONF_UNIT])
    except AuthenticationError as err:
        raise InvalidAuth from err
    except MyDCWaterError as err:
        raise CannotConnect from err

    account = report.account
    unique_id = account.account_number or data[CONF_USERNAME]
    title = account.service_address or account.account_name or unique_id
    return ValidationResult(title=title, unique_id=unique_id)


async def async_validate_input(hass: HomeAssistant, data: dict[str, Any]) -> ValidationResult:
    """Validate the user input allows us to connect."""
    return await hass.async_add_executor_job(_validate_credentials, data)


class MyDCWaterOptionsFlow(OptionsFlowWithConfigEntry):
    """Handle DC Water options."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        defaults = {
            CONF_UNIT: self.config_entry.options.get(
                CONF_UNIT, self.config_entry.data.get(CONF_UNIT, DEFAULT_UNIT)
            ),
        }
        return self.async_show_form(step_id="init", data_schema=_build_options_schema(defaults))


class MyDCWaterConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for DC Water."""

    VERSION = 1

    def __init__(self) -> None:
        self._reauth_entry: ConfigEntry | None = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await async_validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception during mydcwater setup")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(info.unique_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=info.title, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=_build_user_schema(user_input or {}),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> FlowResult:
        """Handle a reauthentication flow."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm updated credentials for an existing entry."""
        assert self._reauth_entry is not None
        errors: dict[str, str] = {}

        defaults = {
            CONF_USERNAME: self._reauth_entry.data.get(CONF_USERNAME, ""),
            CONF_PASSWORD: "",
            CONF_UNIT: self._reauth_entry.options.get(
                CONF_UNIT,
                self._reauth_entry.data.get(CONF_UNIT, DEFAULT_UNIT),
            ),
        }

        if user_input is not None:
            candidate = {
                **self._reauth_entry.data,
                **user_input,
                CONF_UNIT: self._reauth_entry.options.get(
                    CONF_UNIT,
                    self._reauth_entry.data.get(CONF_UNIT, DEFAULT_UNIT),
                ),
            }
            try:
                info = await async_validate_input(self.hass, candidate)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception during mydcwater reauth")
                errors["base"] = "unknown"
            else:
                self.hass.config_entries.async_update_entry(
                    self._reauth_entry,
                    data={
                        **self._reauth_entry.data,
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                    title=info.title,
                )
                await self.hass.config_entries.async_reload(self._reauth_entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME, default=defaults[CONF_USERNAME]): str,
                    vol.Required(CONF_PASSWORD, default=defaults[CONF_PASSWORD]): str,
                }
            ),
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(config_entry: ConfigEntry) -> MyDCWaterOptionsFlow:
        """Return the options flow handler."""
        return MyDCWaterOptionsFlow(config_entry)
