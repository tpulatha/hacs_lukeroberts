"""Luke Roberts integration light platform."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import (
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from pylukeroberts import LUVOLAMP

from .const import DOMAIN
from .models import LEDBLEData, LUVOLAMPData


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the light platform for Luvo Lamp."""
    data: LUVOLAMPData = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([LUVOLAMPEntity(data.coordinator, data.device, entry.title)])


class LUVOLAMPEntity(CoordinatorEntity[DataUpdateCoordinator[None]], LightEntity):
    """Representation of Luvo Lamp device."""

    _attr_supported_color_modes = {ColorMode.ONOFF}
    _attr_has_entity_name = True
    _attr_name = None
    # _attr_supported_features = LightEntityFeature.EFFECT

    def __init__(
        self, coordinator: DataUpdateCoordinator[None], device: LUVOLAMP, name: str
    ) -> None:
        """Initialize an Luvo Lamp."""
        super().__init__(coordinator)
        self._device = device
        self._attr_unique_id = device.address
        self._attr_device_info = DeviceInfo(
            name=name,
            model=f"{device.model_data.description} {hex(device.model_num)}",
            sw_version=hex(device.version_num),
            connections={(dr.CONNECTION_BLUETOOTH, device.address)},
        )
        self._async_update_attrs()

    @callback
    def _async_update_attrs(self) -> None:
        """Handle updating _attr values."""
        device = self._device
        self._attr_color_mode = ColorMode.ONOFF
        # self._attr_brightness = device.brightness
        # self._attr_rgb_color = device.rgb_unscaled
        self._attr_is_on = device.on
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
