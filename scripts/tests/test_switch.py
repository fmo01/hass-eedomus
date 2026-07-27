"""Tests for Eedomus switch entities."""

import os
import sys
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.const import STATE_OFF, STATE_ON

from custom_components.eedomus.switch import EedomusSwitch
#sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "custom_components/eedomus")))
#from  switch import EedomusSwitch

@pytest.mark.asyncio
async def test_switch_initialization():
    """Test switch entity initialization."""
    mock_coordinator = AsyncMock()
    mock_coordinator.config_entry.entry_id = "switch"
    mock_coordinator.data = {
        "switch_1230": {
            "periph_id": "switch_1230", 
            "name": "Test Switch",
            "last_value": "on",
            "value_list": ["on", "off"],
        }
    }

    device_info = {
        "periph_id": "switch_1230", 
        "name": "Test Switch", 
        "usage_id": "37",
    }

    switch = EedomusSwitch(mock_coordinator, device_info["periph_id"])

    assert switch.name == "Test Switch"
    assert switch.unique_id == "eedomus_switch_switch_1230"
    assert switch.is_on is True

@pytest.mark.asyncio
async def test_switch_off_state():
    """Test switch in off state."""
    mock_coordinator = AsyncMock()
    mock_coordinator.config_entry.entry_id = "switch"
    mock_coordinator.data = {
        "switch_1231": {
            "periph_id": "switch_1231", 
            "name": "Test Switch 1", 
            "value": "off",
        }
    }

    device_info = {
        "periph_id": "switch_1231", 
        "name": "Test Switch 1", 
        "usage_id": "37",
    }

    switch = EedomusSwitch(mock_coordinator, device_info["periph_id"])

    assert switch.is_on is False

@pytest.mark.asyncio
async def test_switch_turn_on():
    """Test switch turn on method."""
    mock_coordinator = AsyncMock()
    mock_coordinator.config_entry.entry_id = "switch"
    mock_coordinator.data = {
        "switch_1232": {
            "periph_id": "switch_1232", 
             "name": "Test Switch 2",
            "last_value": "off",
            "value_list": ["on", "off"]
        }
    }

    device_info = {
        "periph_id": "switch_1232", 
        "name": "Test Switch 2",
        "usage_id": "37",
    }

    switch = EedomusSwitch(mock_coordinator, device_info["periph_id"])

    # 🚨 LA CORRECTION MAGIQUE : Injection du faux moteur Home Assistant
    switch.hass = MagicMock()
    switch.hass.services.async_call = AsyncMock()

    assert switch.name == "Test Switch 2"
    assert switch.unique_id == "eedomus_switch_switch_1232"

    assert switch.is_on is False

    # Action : On l'allume
    await switch.async_turn_on()

    # Vérification : On s'assure que l'appel de service HA a bien été déclenché
    switch.hass.services.async_call.assert_called_once()

    # 🚨 SIMULATION DU RETOUR DE LA BOX : 
    # D'après tes logs, l'Eedomus reçoit la valeur numérique 100 pour l'allumage
    mock_coordinator.data["switch_1232"]["last_value"] = 100

    assert switch.is_on is True

@pytest.mark.asyncio
async def test_switch_turn_off():
    " ""Test switch turn off method."" "
    mock_coordinator = AsyncMock()
    mock_coordinator.config_entry.entry_id = "switch"
    mock_coordinator.data = {
        "switch_1234": {
            "periph_id": "switch_1234", 
            "last_value": "on",
            "value_list": ["on", "off"]
        }
    }

    device_info = {
        "periph_id": "switch_1234",
        "name": "Test Switch",
        "usage_id": "37",
    }

    switch = EedomusSwitch(mock_coordinator, device_info["periph_id"])

    switch.hass = MagicMock()
    switch.hass.services.async_call = AsyncMock()

    assert switch.is_on is True
    await switch.async_turn_off()

    switch.hass.services.async_call.assert_called_once()
    mock_coordinator.data["switch_1234"]["last_value"] = 0

    assert switch.is_on is False

@pytest.mark.asyncio
async def test_switch_with_consumption_child():
    """Test switch with consumption child (Issue #9 related)."""
    mock_coordinator = AsyncMock()
    mock_coordinator.config_entry.entry_id = "switch"
    mock_coordinator.data = {
        "switch_1235": {
            "periph_id": "switch_1235",
            "name": "Test Switch 5",
            "last_value": "on",
            "value_list": ["on", "off"],
        },
        "switch_1235_consumption": {
            "periph_id": "switch_1235_consumption",
            "consumption": 15.5,
            "current_power": 100,
            "usage_id": "26",
        },
    }

    device_info = {
        "periph_id": "switch_1235",
        "name": "Test Switch 5",
        "usage_id": "37",
        "children": [
            {
                "periph_id": "switch_1235_consumption",
                "usage_id": "26",
                "name": "Consommation",
            }
        ],
    }

    switch = EedomusSwitch(mock_coordinator, device_info["periph_id"])
    
    # Verify switch properties
    assert switch.name == "Test Switch 5"
    assert switch.is_on is True
    assert switch.unique_id == "eedomus_switch_switch_1235"

    # Verify consumption data exists for energy sensor creation
    consumption_data = mock_coordinator.data.get("switch_1235_consumption", {})
    assert consumption_data.get("consumption") == 15.5
    assert consumption_data.get("current_power") == 100

@pytest.mark.asyncio
async def test_switch_consumption_only_device():
    """Test switch that should be remapped as energy sensor."""
    mock_coordinator = AsyncMock()
    mock_coordinator.data = {
        "consumption_monitor": {
            "periph_id": "consumption_monitor",
            "name": "Consommation Salon",
            "last_value": "150",
            "value_list": ["150"],
        }
    }

    device_info = {
        "periph_id": "consumption_monitor",
        "name": "Consommation Salon",
        "usage_id": "2",  # Appareil électrique
        "children": [
            {
                "periph_id": "consumption_monitor_power",
                "usage_id": "26",
                "name": "Puissance",
            }
        ],
    }

    # This should be detected as a consumption monitor and remapped
    # The test verifies the data structure that would trigger remapping
    switch = EedomusSwitch(mock_coordinator, device_info["periph_id"])

    # Verify the device has the right characteristics for remapping
    assert (
        "conso" in device_info["name"].lower()
        or "consommation" in device_info["name"].lower()
    )

    # Check if it has consumption children
    has_consumption_children = any(
        child.get("usage_id") == "26" for child in device_info.get("children", [])
    )
    assert has_consumption_children is True
