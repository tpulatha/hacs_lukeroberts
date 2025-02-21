"""Support for generic bluetooth devices."""

import logging

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from pylukeroberts import LUVOLAMP

from .const import DOMAIN
from .coordinator import LukeRobertsBTCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.LIGHT]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Luke Roberts Luvo Light from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    address: str = entry.data[CONF_ADDRESS]
    ble_device = bluetooth.async_ble_device_from_address(hass, address.upper(), True)
    if not ble_device:
        error_msg = f"Could not find Generic BT Device with address {address}"
        raise ConfigEntryNotReady(error_msg)

    # Create the LUVOLAMP device first
    _LOGGER.warning(f"Created device {ble_device.address}")
    device = LUVOLAMP(ble_device)
    _LOGGER.warning(f"Created lamp {device._ble_device.address}")
    coordinator = hass.data[DOMAIN][entry.entry_id] = LukeRobertsBTCoordinator(
        hass, _LOGGER, ble_device, device, entry.title, entry.unique_id, True
    )
    entry.async_on_unload(coordinator.async_start())

    if not await coordinator.async_wait_ready():
        error_msg = f"{address} is not advertising state"
        raise ConfigEntryNotReady(error_msg)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.config_entries.async_entries(DOMAIN):
            hass.data.pop(DOMAIN)

    return unload_ok
