"""Tests for Eedomus sensor entities."""

import os
import sys
from unittest.mock import AsyncMock, patch , MagicMock

import pytest
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import UnitOfEnergy, UnitOfPower, UnitOfTemperature

from custom_components.eedomus.sensor import EedomusSensor, EedomusBatterySensor
#sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "custom_components/eedomus")))
#from sensor import EedomusSensor, EedomusBatterySensor


@pytest.mark.asyncio
async def test_temperature_sensor():
    """Test temperature sensor."""
    mock_coordinator = AsyncMock()
    mock_coordinator.config_entry.entry_id = "sensor"
    mock_coordinator.data = {
        "temp_sensor": {
            "periph_id": "temp_sensor",
            "name": "Temperature Sensor",
            "last_value": 22.5,
            "value": 22.5,
            "unit": "°C",
            "usage_id": "7",
        }
    }

    device_info = {
        "periph_id": "temp_sensor",
        "name": "Temperature Sensor",
        "usage_id": "7",
    }

    #sensor = EedomusSensor(mock_coordinator, device_info)
    
    # 1. Instanciation du capteur
    sensor = EedomusSensor(mock_coordinator, device_info["periph_id"])
    # # 🔥 ANNIHILER L'ÉCRITURE D'ÉTAT POUR LE TEST UNITAIRE
    # sensor.async_write_ha_state = lambda: None

    # # 🔥 2. FORCER LA MISE À JOUR DES DONNÉES DEPUIS LE COORDINATEUR
    # sensor._handle_coordinator_update()

    assert sensor.name == "Temperature Sensor"
    assert sensor.unique_id == "eedomus_sensor_temp_sensor"
    assert sensor.device_class == SensorDeviceClass.TEMPERATURE
    assert sensor.native_unit_of_measurement == UnitOfTemperature.CELSIUS
    assert sensor.native_value == 22.5

@pytest.mark.asyncio
async def test_temperature_sensor_with_battery():
    """Test temperature sensor."""
    mock_coordinator = AsyncMock()
    mock_coordinator.config_entry.entry_id = "sensor"
    mock_coordinator.data = {
        "temp_sensor": {
            "periph_id": "temp_sensor",
            "name": "Temperature Sensor",
            "last_value": 22.5,
            "value": 22.5,
            "unit": "°C",
            "battery": 75,
            "usage_id": "7",
        }
    }

    device_info = {
        "periph_id": "temp_sensor",
        "name": "Temperature Sensor",
        "usage_id": "7",
    }

    
    sensor = EedomusSensor(mock_coordinator, device_info["periph_id"])

    assert sensor.name == "Temperature Sensor"
    assert sensor.unique_id == "eedomus_sensor_temp_sensor"
    assert sensor.device_class == SensorDeviceClass.TEMPERATURE
    assert sensor.native_unit_of_measurement == UnitOfTemperature.CELSIUS
    assert sensor.native_value == 22.5
    assert sensor.unique_id == f"eedomus_sensor_{device_info['periph_id']}"

    battery_sensor = EedomusBatterySensor(mock_coordinator, device_info["periph_id"])

    assert battery_sensor.name == "Temperature Sensor Battery"  # Ou "Capteur Salon Batterie"
    assert battery_sensor.device_class == SensorDeviceClass.BATTERY
    assert battery_sensor.native_unit_of_measurement == "%"
    assert battery_sensor.native_value == 75
    assert battery_sensor.unique_id == f"eedomus_sensor_{device_info['periph_id']}_battery"

@pytest.mark.asyncio
async def test_humidity_sensor():
    """Test humidity sensor."""
    mock_coordinator = AsyncMock()
    mock_coordinator.data = {
        "humidity_sensor": {
            "periph_id": "humidity_sensor",
            "name": "Humidity Sensor",
            "value": 45.0,
            "last_value": 45.0,
            "value_type": "float",
            "unit": "%",
            "usage_id": "22",
        }
    }

    device_info = {
        "periph_id": "humidity_sensor",
        "name": "Humidity Sensor",
        "usage_id": "22",
    }

    # sensor = EedomusSensor(mock_coordinator, device_info)
    sensor = EedomusSensor(mock_coordinator, device_info["periph_id"])

    assert sensor.device_class == SensorDeviceClass.HUMIDITY
    assert sensor.native_unit_of_measurement == "%"
    assert sensor.native_value == 45.0


@pytest.mark.asyncio
async def test_power_sensor():
    """Test power sensor."""
    mock_coordinator = AsyncMock()
    mock_coordinator.data = {
        "power_sensor": {
            "periph_id": "power_sensor",
            "name": "Power Sensor",
            "value": 150.5,
            "last_value": 150.5,
            "unit": "W",
            "usage_id": "28",
        }
    }

    device_info = {
        "periph_id": "power_sensor",
        "name": "Power Sensor",
        "usage_id": "28",
    }

    #sensor = EedomusSensor(mock_coordinator, device_info)
    sensor = EedomusSensor(mock_coordinator, device_info["periph_id"])

    assert sensor.device_class == SensorDeviceClass.POWER
    assert sensor.native_unit_of_measurement == UnitOfPower.WATT
    assert sensor.native_value == 150.5


@pytest.mark.asyncio
async def test_energy_sensor():
    """Test energy sensor (Issue #9)."""
    mock_coordinator = AsyncMock()
    mock_coordinator.data = {
        "energy_sensor": {
            "periph_id": "energy_sensor",
            "name": "Energy Sensor",
            "value": 12.5,
            "last_value": 12.5,
            "unit": "Wh",
            "usage_id": "26",
        }
    }

    device_info = {
        "periph_id": "energy_sensor",
        "name": "Energy Sensor",
        "usage_id": "26",
    }

    sensor = EedomusSensor(mock_coordinator, device_info["periph_id"])

    assert sensor.device_class == SensorDeviceClass.ENERGY
    assert sensor.native_unit_of_measurement == UnitOfEnergy.WATT_HOUR
    assert sensor.native_value == 12.5


@pytest.mark.asyncio
async def test_battery_sensor():
    """Test battery sensor."""
    mock_coordinator = AsyncMock()
    mock_coordinator.config_entry.entry_id = "sensor"
    mock_coordinator.data = {
        "temp_unknown_sensor": {
            "periph_id": "temp_unknown_sensor",
            "name": "Battery Level",
            "last_value": 22.5,
            "value": 22.5,
            "unit": "°C",
            "battery": 75,
            "usage_id": "7",
        }
    }

    device_info = {
        "periph_id": "temp_unknown_sensor",
        "name": "Battery Level",
        "usage_id": "7",
    }

    sensor = EedomusSensor(mock_coordinator, device_info["periph_id"])
    sensor_b = EedomusBatterySensor(mock_coordinator, device_info["periph_id"])

    assert sensor_b.name == "Battery Level Battery"
    assert sensor_b.device_class == SensorDeviceClass.BATTERY
    assert sensor_b.native_unit_of_measurement == "%"
    assert sensor_b.native_value == 75
    assert sensor_b.unique_id == f"eedomus_sensor_{device_info['periph_id']}_battery"


@pytest.mark.asyncio
async def test_sensor_with_missing_data():
    """Test sensor with missing value."""
    mock_coordinator = AsyncMock()
    mock_coordinator.config_entry.entry_id = "sensor"
    mock_coordinator.get_yaml_config_sync = MagicMock(return_value={})
    mock_coordinator.data = {
        "missing_sensor": {
            "periph_id": "missing_sensor", 
            "name": "Missing Data Sensor"
            # No value field
        }
    }

    device_info = {
        "periph_id": "missing_sensor", 
        "name": "Missing Data Sensor",
    }

    sensor = EedomusSensor(mock_coordinator, device_info["periph_id"])

    assert sensor.native_value is None


@pytest.mark.asyncio
async def test_sensor_update():
    """Test sensor update mechanism."""
    mock_coordinator = AsyncMock()
    mock_coordinator.config_entry.entry_id = "sensor"
    mock_coordinator.data = {
        "temp_sensor": {
          "periph_id": "temp_sensor",
          "name": "Temperature Sensor",
          "value": 20.0,
          "value": 20.0,
          "last_value": 20.0,
          "usage_id": "7",
        }
    }

    device_info = {
        "periph_id": "temp_sensor",
        "name": "Temperature Sensor",
        "usage_id": "7",
    }

    sensor = EedomusSensor(mock_coordinator, device_info["periph_id"])

    # Initial value
    assert sensor.native_value == 20.0

    # Simulate update
    mock_coordinator.data["temp_sensor"]["last_value"] = 22.5

    # Value should update
    assert sensor.native_value == 22.5
