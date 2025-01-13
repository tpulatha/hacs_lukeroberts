"""The led ble integration models."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pylukeroberts import LUVOLAMP


@dataclass
class LUVOLAMPData:
    """Data for the led ble integration."""

    title: str
    device: LUVOLAMP
    coordinator: DataUpdateCoordinator[None]
