# DC Water for Home Assistant

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=will-tm&repository=ha_mydcwater&category=integration)

Custom HACS integration for exposing `mydcwater.com` meter readings in Home Assistant.

The integration uses [`pymydcwater`](https://github.com/will-tm/pymydcwater) to authenticate against the DC Water portal during config entry setup and then refreshes data once per hour. Credentials are entered once during account setup and stored in the Home Assistant config entry.

## Features

- Config-entry based setup from the Home Assistant UI
- Hourly polling against the mydcwater portal
- Sensors for latest meter reading, latest daily usage, and rolling averages
- HACS-ready repository layout

## Installation

### HACS

1. Open the HACS button above.
2. Add the repository as an `Integration` if prompted.
3. Install `DC Water`.
4. Restart Home Assistant.
5. Go to `Settings -> Devices & services -> Add integration`.
6. Search for `DC Water` and enter your mydcwater `User ID`, password, and preferred unit.

### Manual

1. Copy `custom_components/mydcwater` into your Home Assistant `custom_components` directory.
2. Restart Home Assistant.
3. Add the `DC Water` integration from `Settings -> Devices & services`.

## Exposed Sensors

- `Latest meter reading`
- `Latest daily usage`
- `Daily average`
- `Annual average`
- `Latest reading timestamp`

## Notes

- The integration does not fetch data more often than once per hour.
- `CuFt` and `Gal` are exposed as Home Assistant water-volume sensors.
- `CCF` is supported, but Home Assistant treats it as a generic unit instead of a water device-class unit.
