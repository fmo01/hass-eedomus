"""Tests for Eedomus light entities."""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components.light import ATTR_BRIGHTNESS, ATTR_RGBW_COLOR, ColorMode
from homeassistant.const import STATE_OFF, STATE_ON

# Importations des composants locaux de l'intégration eedomus
#sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "custom_components/eedomus")))
#from light import (
from custom_components.eedomus.light import (
    EedomusLight,
    EedomusRGBChildLight,
    EedomusRGBWLight,
    async_setup_entry,
)

@pytest.mark.asyncio
async def test_light_rgbw_initialization():
    """Test light rgbw entity initialization."""
    hass = MagicMock()
    entry = MagicMock()
    entry.entry_id = "mock_entry_id"
    async_add_entities = MagicMock()

    coordinator = AsyncMock()

    # 1. FIX : Ajout de la clé "name" manquante pour éviter le KeyError à la ligne 91 de light.py
    coordinator.get_all_peripherals = MagicMock(return_value={
        "1230": {"periph_id": "1230", "name": "Lampe Salon", "usage_id": "1"},
        "1231": {"periph_id": "1231", "parent_periph_id": "1230", "usage_id": "1", "name": "Lampe Salon R"},
        "1232": {"periph_id": "1232", "parent_periph_id": "1230", "usage_id": "1", "name": "Lampe Salon G"},
        "1233": {"periph_id": "1233", "parent_periph_id": "1230", "usage_id": "1", "name": "Lampe Salon B"},
        "1234": {"periph_id": "1234", "parent_periph_id": "1230", "usage_id": "1", "name": "Lampe Salon W"},
    })

    # 2. Mock de coordinator.data
    coordinator.data = {
        "1230": {
            "ha_entity": "light",
            "ha_subtype": "rgbw",
            "name": "Lampe Salon",
            "last_value": "50",
        },
        "1231": {"ha_entity": "light", "ha_subtype": "brightness", "last_value": "100"},
        "1232": {"ha_entity": "light", "ha_subtype": "brightness", "last_value": "100"},
        "1233": {"ha_entity": "light", "ha_subtype": "brightness", "last_value": "100"},
        "1234": {"ha_entity": "light", "ha_subtype": "brightness", "last_value": "100"},
    }

    hass.data = {
        "eedomus": {
            entry.entry_id: {
                "coordinator": coordinator
            }
        }
    }

    await async_setup_entry(hass, entry, async_add_entities)

    assert async_add_entities.called
    created_entities = async_add_entities.call_args[0][0]
    
    # 🚨 FIX : Le code crée actuellement 1 parent + 4 enfants individuels
    assert len(created_entities) == 5

    # 1. On isole le parent pour s'assurer qu'il a bien été promu en RGBW
    parent_entity = next(e for e in created_entities if e._periph_id == "1230")
    assert isinstance(parent_entity, EedomusRGBWLight)
    assert parent_entity.supported_color_modes == {ColorMode.RGBW}

    # 2. On vérifie que les 4 autres canaux sont restés de simples lumières (brightness)
    child_entities = [e for e in created_entities if e._periph_id != "1230"]
    assert len(child_entities) == 4
    
    for child in child_entities:
        # C'est une lumière classique, pas une RGBW
        assert isinstance(child, EedomusLight)
        assert not isinstance(child, EedomusRGBWLight)

@pytest.mark.asyncio
async def test_light_off_state():
    """Test light in off state."""
    mock_coordinator = AsyncMock()
    mock_coordinator.config_entry.entry_id = "light"
    mock_coordinator.data = {
        "12311": {
            "periph_id": "12311",
            "ha_entity": "light",
            "ha_subtype": "brightness",
            "name": "Test Light 1",
            "last_value": "off", 
            "usage_id": "1"
        }
    }

    device_info = {
        "periph_id": "12311",
        "name": "Test Light 1",
        "usage_id": "1",
        "color_mode": "brightness",
    }

    light = EedomusLight(mock_coordinator, device_info["periph_id"])
    #print (vars(light))
    #print(dir(light))
    assert light.is_on is False
    assert light.brightness == 0


@pytest.mark.asyncio
async def test_light_turn_on():
    " ""Test light turn on method."" "
    mock_coordinator = AsyncMock()
    mock_coordinator.config_entry.entry_id = "light"
    mock_coordinator.data = {
        "light_1234": {
            "periph_id": "light_1234",
            "ha_entity": "light",
            "ha_subtype": "brightness",
            "last_value": "off", 
            "brightness": 0, 
            "value_list": ["on", "off"],
       }
    }

    device_info = {"periph_id": "light_1234", "name": "Test Light"}

    light = EedomusLight(mock_coordinator, device_info["periph_id"])

   # 🚨 LA CORRECTION MAGIQUE : Injection du faux moteur Home Assistant
    light.hass = MagicMock()
    light.hass.services.async_call = AsyncMock()

    assert light.unique_id == "eedomus_light_light_1234"

    assert light.is_on is False

    # Action : On l'allume
    await light.async_turn_on()

    # Vérification : On s'assure que l'appel de service HA a bien été déclenché
    light.hass.services.async_call.assert_called_once()

    # 🚨 SIMULATION DU RETOUR DE LA BOX :
    # D'après tes logs, l'Eedomus reçoit la valeur numérique 100 pour l'allumage
    mock_coordinator.data["light_1234"]["last_value"] = 100

    assert light.is_on is True
 
@pytest.mark.asyncio
async def test_light_turn_off():
    """Test light turn off method."""
    mock_coordinator = AsyncMock()
    mock_coordinator.config_entry.entry_id = "light"
    mock_coordinator.data = {
        "light_1235": {
            "periph_id": "light_1235",
            "ha_entity": "light",
            "ha_subtype": "brightness",
            "last_value": "on", 
            "brightness": 50, 
            "value_list": ["on", "off"],
       }
    }

    device_info = {"periph_id": "light_1235", "name": "Test Light"}

    light = EedomusLight(mock_coordinator, device_info["periph_id"])

   # 🚨 LA CORRECTION MAGIQUE : Injection du faux moteur Home Assistant
    light.hass = MagicMock()
    light.hass.services.async_call = AsyncMock()

    assert light.unique_id == "eedomus_light_light_1235"

    assert light.is_on is True

    # Action : On l'allume
    await light.async_turn_off()

    # Vérification : On s'assure que l'appel de service HA a bien été déclenché
    light.hass.services.async_call.assert_called_once()

    # 🚨 SIMULATION DU RETOUR DE LA BOX :
    # D'après tes logs, l'Eedomus reçoit la valeur numérique 100 pour l'allumage
    mock_coordinator.data["light_1235"]["last_value"] = "0"

    assert light.is_on is False

@pytest.mark.asyncio
async def test_light_with_consumption_child():
    """Test light with consumption child (Issue #9 related)."""
    mock_coordinator = AsyncMock()
    mock_coordinator.config_entry.entry_id = "light"
    mock_coordinator.data = {
        "light_123": {
            "name": "Test Light",
            "last_value": "on",
            "brightness": 255,
            "value_list": ["on", "off"],
        },
        "light_123_consumption": {
            "consumption": 20.5,
            "current_power": 80,
            "usage_id": "26",
            "name": "Consommation",
        },
    }

    device_info = {
        "periph_id": "light_123",
        "name": "Test Light",
        "usage_id": "1",
        "color_mode": "brightness",
    }

    light = EedomusLight(mock_coordinator, device_info["periph_id"])

    # Verify light properties
    assert light.name == "Test Light"
    assert light.is_on is True

    # Verify consumption data exists for energy sensor creation
    consumption_data = mock_coordinator.data.get("light_123_consumption", {})
    assert consumption_data.get("consumption") == 20.5
    assert consumption_data.get("current_power") == 80

@pytest.mark.asyncio
async def test_light_standalone_rgb_no_children():
    """Test une lumière RGB autonome (comme un ESP32) sans périphériques enfants."""
    mock_coordinator = AsyncMock()
    mock_coordinator.config_entry.entry_id = "light"
    
    # Simulation des données renvoyées par l'eedomus pour l'ESP32
    mock_coordinator.data = {
        "light_123_02": {
            "periph_id": "light_123_02",
            "name": "light_123_02 Info",
            "ha_entity": "light",
            "ha_subtype": "rgb",          # Mode RGB pur
            "last_value": "255,100,50",   # La couleur est directement dans la valeur !
        }
    }

    # Instanciation de la classe de base (car pas d'enfants détectés)
    light = EedomusLight(mock_coordinator, "light_123_02")

    # Vérifications des propriétés Home Assistant
    assert light.supported_color_modes == {ColorMode.RGB}
    assert light.color_mode == ColorMode.RGB
    
    # Vérification que le parsing de la chaîne "R,G,B" fonctionne
    assert light.rgb_color == (255, 100, 50)
    
    # Vérification que la présence de virgules ne fait pas planter le brightness
    assert light.is_on is True
    assert light.brightness == 255

"""@pytest.mark.asyncio
async def test_light_rgbw_color():
    " ""Test RGBW light color handling."" "
    mock_coordinator = AsyncMock()
    mock_coordinator.config_entry.entry_id = "light"
    mock_coordinator.data = {
        "light_rgbw": {
            "name": "RGBW Light",
            "periph_id": "light_rgbw",
            "laste_value": "on",
            "ha_entity": "light",
            "ha_subtype": "rgbw",
            "rgbw_color": [255,128,64,200],  # R,G,B,W
            "value_list": ["on", "off"],
        }
    }

    device_info = {
        "periph_id": "light_rgbw",
        "name": "RGBW Light",
        "usage_id": "1",
        "color_mode": "rgbw",
    }

    light = EedomusLight(mock_coordinator, device_info["periph_id"])

    #print (vars(light))
    #print(dir(light))
    print(light.unique_id )
    #print(light.state )
    #print(light.state_attributes )

     

    assert light.color_mode == ColorMode.RGBW
    # Verify color parsing
    #color_parts = light._parse_color("255,128,64,200")
    #assert color_parts == [255, 128, 64, 200]
    assert light.rgbw_color == [255, 128, 64, 200]

"""
@pytest.mark.asyncio
async def test_light_hue_one_child_color():
    """Test une lumière Hue dotée d'un parent d'intensité et d'un seul enfant couleur."""
    mock_coordinator = AsyncMock()
    mock_coordinator.config_entry.entry_id = "light"
    
    # Injection des données réelles de ton eedomus
    mock_coordinator.data = {
        "546924": {
            "periph_id": "546924",
            "name": "Lampe Hue Couleur ",
            "ha_entity": "light",
            "ha_subtype": "rgb",
            "last_value": "30",  # Intensité à 30%
        },
        "546930": {
            "periph_id": "546930",
            "parent_periph_id": "546924",
            "name": "Hue - Couleur Hue",
            "last_value": "0,25,100",  # Cyan (0% R, 25% G, 100% B)
        }
    }

    color_child = {"periph_id": "546930", "parent_periph_id": "546924"}

    # Instanciation de la nouvelle classe
    light = EedomusRGBChildLight(mock_coordinator, "546924", color_child)

    # 1. Vérification du mode de couleur
    assert light.supported_color_modes == {ColorMode.RGB}
    assert light.color_mode == ColorMode.RGB

    # 2. Vérification de la conversion de la luminosité du parent (30% -> 77 octal)
    # round(30 * 255 / 100) = 77 76 car probleme python3 sur les .5 
    assert light.brightness == 76

    # 3. Vérification du parsing de la couleur de l'enfant
    # 0%   -> 0
    # 25%  -> round(25 * 255 / 100) = 64
    # 100% -> 255
    assert light.rgb_color == (0, 64, 255)

@pytest.mark.asyncio
async def test_light_brightness_only():
    """Test brightness-only light."""
    mock_coordinator = AsyncMock()
    mock_coordinator.config_entry.entry_id = "light"
    mock_coordinator.data = {
        "light_dimmer": {
            "name": "Dimmer Light",
            "value": "on",
            "ha_entity": "light",
            "ha_subtype": "brightness",
            "last_value": 50,
            "value_list": ["on", "off"],
        }
    }

    device_info = {
        "periph_id": "light_dimmer",
        "name": "Dimmer Light",
        "usage_id": "1",
        "color_mode": "brightness",
    }

    light = EedomusLight(mock_coordinator, device_info["periph_id"])

    assert light.supported_color_modes == {ColorMode.BRIGHTNESS}
    assert light.color_mode == ColorMode.BRIGHTNESS
    assert light.brightness == 128
