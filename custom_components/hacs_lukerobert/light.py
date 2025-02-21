import asyncio
import logging

from homeassistant.components.light import LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from pyLukeRoberts import Lamp  # Import your library

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Luke Roberts Lamp from a config entry."""
    mac_address = config_entry.data["mac_address"]
    lamp = Lamp(mac_address)
    try:
        # Connect to the lamp and get initial state
        await lamp.async_connect()
        initial_state = (
            await lamp.async_get_state()
        )  # Assumes this returns a dict with 'is_on'
    except Exception as e:
        _LOGGER.error(f"Failed to connect to lamp {mac_address}: {e}")
        return  # Skip adding the entity if connection fails
    entity = LukeRobertsLamp(lamp, initial_state, mac_address)
    async_add_entities([entity])
    # Store the lamp instance for cleanup during unload
    hass.data[DOMAIN][config_entry.entry_id] = lamp


class LukeRobertsLamp(LightEntity):
    """Representation of a Luke Roberts Lamp."""

    def __init__(self, lamp, initial_state, mac_address):
        """Initialize the lamp entity."""
        self._lamp = lamp
        self._is_on = initial_state.get(
            "is_on", False
        )  # Default to False if state unavailable
        self._mac_address = mac_address
        self._attr_unique_id = mac_address  # Use MAC as unique ID
        self._listener_task = None

    @property
    def name(self) -> str:
        """Return the name of the lamp."""
        return f"Luke Roberts Lamp {self._mac_address}"

    @property
    def is_on(self) -> bool:
        """Return true if the lamp is on."""
        return self._is_on

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for Home Assistant device registry."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._mac_address)},
            name=f"Luke Roberts Lamp {self._mac_address}",
            manufacturer="Luke Roberts",
            model="Smart Lamp",
        )

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the lamp on."""
        try:
            await self._lamp.async_turn_on()
            self._is_on = True  # Optimistic update
            self.async_write_ha_state()
        except Exception as e:
            _LOGGER.error(f"Error turning on lamp {self._mac_address}: {e}")

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the lamp off."""
        try:
            await self._lamp.async_turn_off()
            self._is_on = False  # Optimistic update
            self.async_write_ha_state()
        except Exception as e:
            _LOGGER.error(f"Error turning off lamp {self._mac_address}: {e}")

    async def async_added_to_hass(self) -> None:
        """Start listening for state changes when added to Home Assistant."""

        def state_update_callback(new_state):
            self._is_on = new_state.get("is_on", self._is_on)
            self.async_write_ha_state()

        self._listener_task = asyncio.create_task(
            self._lamp.async_listen(state_update_callback)
        )

    async def async_will_remove_from_hass(self) -> None:
        """Clean up when removed from Home Assistant."""
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
