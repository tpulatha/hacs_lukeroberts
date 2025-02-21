"""Luke Roberts integration light platform."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

from homeassistant.components.light import (
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN
from .coordinator import LukeRobertsBTCoordinator

if TYPE_CHECKING:
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from pylukeroberts import LUVOLAMP


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the light platform for Luvo Lamp."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([LUVOLAMPEntity(coordinator, coordinator.device, entry.title)])


# class LUVOLAMPEntity(BluetoothCoordinatorEntity[LukeRobertsBTCoordinator], LightEntity):
class LUVOLAMPEntity(CoordinatorEntity[DataUpdateCoordinator[None]], LightEntity):
    """Representation of Luvo Lamp device."""

    _attr_supported_color_modes: ClassVar[set[ColorMode]] = {
        ColorMode.ONOFF  # ,
        # ColorMode.BRIGHTNESS,
        # ColorMode.RGB,
    }
    _attr_has_entity_name: ClassVar[bool] = True
    _attr_name: ClassVar[str | None] = None
    # _attr_supported_features = LightEntityFeature.EFFECT

    def __init__(
        self, coordinator: LukeRobertsBTCoordinator, device: LUVOLAMP, name: str
    ) -> None:
        """Initialize an Luvo Lamp."""
        super().__init__(coordinator)
        self._device = device
        self._attr_unique_id = coordinator.address
        self._attr_device_info = DeviceInfo(
            name=name,
            model="Luke Roberts Lamp",
            connections={(dr.CONNECTION_BLUETOOTH, coordinator.address)},
        )
        self._async_update_attrs()

    @callback
    def _async_update_attrs(self) -> None:
        """Handle updating _attr values."""
        device = self._device
        self._attr_color_mode = ColorMode.ONOFF
        # self._attr_brightness = device.brightness
        # self._attr_rgb_color = device.rgb_unscaled
        self._attr_is_on = device._isOn
        # self._attr_effect = device.effect
        # self._attr_effect_list = device.effect_list

    # async def _async_set_effect(self, effect: str, brightness: int) -> None:
    #     """Set an effect."""
    #     await self._device.async_set_effect(
    #         effect,
    #         self._device.speed or DEFAULT_EFFECT_SPEED,
    #         round(brightness / 255 * 100),
    #     )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Instruct the light to turn on."""
        await self._device.switch_on()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Instruct the light to turn off."""
        _LOGGER.warning(
            f"Turning off device with address: {self._device._ble_device.address}"
        )
        await self._device.switch_off()

    @callback
    def _handle_coordinator_update(self, *args: Any) -> None:
        """Handle data update."""
        self._async_update_attrs()
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        self.async_on_remove(
            self._device.register_callback(self._handle_coordinator_update)
        )
        return await super().async_added_to_hass()
