"""Tests for Eedomus cover entities."""

import os
import sys
from unittest.mock import AsyncMock, patch , MagicMock

import pytest
from homeassistant.components.cover import CoverDeviceClass, CoverEntityFeature
from homeassistant.const import STATE_CLOSED, STATE_CLOSING, STATE_OPEN, STATE_OPENING

from custom_components.eedomus.cover import EedomusCover
#sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "custom_components/eedomus")))
#print(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "custom_components/eedomus")))
#from cover import EedomusCover


@pytest.mark.asyncio
async def test_cover_initialization():
    """Test cover entity initialization."""
    mock_coordinator = AsyncMock()
    mock_coordinator.config_entry.entry_id = "cover"
    mock_coordinator.data = {
        "cover_1230": {
            "periph_id": "cover_1230",
            "name": "Test Cover 0",
            "last_value": "100",
            "position": 100,
            "tilt_position": 50,
        }
    }

    device_info = {"periph_id": "cover_1230", "name": "Test Cover 0", "usage_id": "48"}

    cover = EedomusCover(mock_coordinator, device_info["periph_id"])
    print (vars(cover))
    print(dir(cover))
    assert cover.name == "Test Cover 0"
    assert cover.unique_id == "eedomus_cover_cover_1230"
    assert cover.is_closed is False
    assert cover.current_cover_position == 100
    assert cover.current_cover_tilt_position == 50
    assert cover.supported_features == (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.STOP
        | CoverEntityFeature.SET_POSITION
        | CoverEntityFeature.SET_TILT_POSITION
    )


@pytest.mark.asyncio
async def test_cover_closed_state():
    """Test cover in closed state."""
    mock_coordinator = AsyncMock()
    mock_coordinator.config_entry.entry_id = "cover"
    mock_coordinator.data = {"cover_1231": {"periph_id": "cover_1231", "last_value": "closed", "position": 0}}

    device_info = {"periph_id": "cover_1231", "name": "Test Cover"}

    cover = EedomusCover(mock_coordinator, device_info["periph_id"])

    assert cover.is_closed is True
    assert cover.current_cover_position == 0


@pytest.mark.asyncio
async def test_cover_open_method():
    """Test cover open method."""
    mock_coordinator = AsyncMock()
    mock_coordinator.config_entry.entry_id = "cover"
    mock_coordinator.data = {"cover_123": { "periph_id": "cover_123", "last_value": "closed", "position": 0}}

    device_info = {"periph_id": "cover_123", "name": "Test Cover"}

    cover = EedomusCover(mock_coordinator, device_info["periph_id"])
    
    
    assert cover.is_closed is True
    assert cover.current_cover_position == 0
    with patch.object(cover, "async_set_value") as mock_set_value:
        # On déclenche l'ouverture
        await cover.async_open_cover()
            
        # On vérifie que async_set_value a bien été appelée avec "100" 
        # (car async_open_cover demande la position 100, convertie en string par ta méthode)
        mock_set_value.assert_called_once_with("100")
    # SIMULATION DU RETOUR DE L'API :
    # Dans la vraie vie, l'Eedomus mettrait à jour sa valeur et le coordinateur la récupérerait.
    # Ici, on modifie manuellement la donnée du mock pour simuler ce rafraîchissement.
    mock_coordinator.data["cover_123"]["last_value"] = "100"
    mock_coordinator.data["cover_123"]["position"] = 100
    # On peut maintenant vérifier que l'entité interprète correctement le nouvel état
    assert cover.is_closed is False
    assert cover.current_cover_position == 100

@pytest.mark.asyncio
async def test_cover_set_position():
    """Test cover set position method."""
    mock_coordinator = AsyncMock()
    mock_coordinator.config_entry.entry_id = "cover"
    mock_coordinator.data = {"cover_123": {"periph_id": "cover_123", "last_value": "50", "position": 50}}

    device_info = {"periph_id": "cover_123", "name": "Test Cover"}

    cover = EedomusCover(mock_coordinator, device_info["periph_id"])

    assert cover.is_closed is False
    assert cover.current_cover_position == 50
    with patch.object(cover, "async_set_value") as mock_set_value:
        await cover.async_set_cover_position(position=75)
        mock_set_value.assert_called_once_with("75")
    mock_coordinator.data["cover_123"]["last_value"] = "75"
    mock_coordinator.data["cover_123"]["position"] = 75
    # On peut maintenant vérifier que l'entité interprète correctement le nouvel état
    assert cover.is_closed is False
    assert cover.current_cover_position == 75


@pytest.mark.asyncio
async def test_cover_with_energy_sensor():
    """Test cover with associated energy sensor (Issue #9 related)."""
    mock_coordinator = AsyncMock()
    mock_coordinator.config_entry.entry_id = "cover"
    mock_coordinator.data = {
        "cover_123": {"periph_id": "cover_123", "name": "Test Cover", "value": "open", "position": 100},
        "cover_123_consumption": {"periph_id": "cover_123_consumption", "consumption": 25.5, "current_power": 50},
    }

    device_info = {
        "periph_id": "cover_123",
        "name": "Test Cover",
        "usage_id": "48",
        "children": [{"periph_id": "cover_123_consumption", "usage_id": "26"}],
    }

    cover = EedomusCover(mock_coordinator, device_info["periph_id"])

    # Verify cover properties
    assert cover.name == "Test Cover"

    # Verify energy sensor would be created for consumption child
    # This is handled in the coordinator setup, but we can verify the data exists
    consumption_data = mock_coordinator.data.get("cover_123_consumption", {})
    assert consumption_data.get("consumption") == 25.5


@pytest.mark.asyncio
async def test_cover_with_missing_parent2():
    """Test cover when parent device is not loaded."""
    mock_coordinator = AsyncMock()
    mock_coordinator.config_entry.entry_id = "cover"
        
    # 1. Correction de la donnée (utilisation de 'last_value' avec une valeur numérique)
    mock_coordinator.data = {
        "cover_child": {
            "name": "Child Cover", 
            "last_value": "0", 
            "position": 0, 
            "parent_periph_id": "missing_parent"
        }
        # Note: missing_parent is NOT in coordinator.data
    }

    device_info = {
        "periph_id": "cover_child",
        "name": "Child Cover",
        "usage_id": "48",
        "parent_periph_id": "missing_parent"
    }

    # L'instanciation ne doit pas lever de KeyError
    cover = EedomusCover(mock_coordinator, device_info["periph_id"])

    # 2. Vérification des propriétés de base
    assert cover.name == "Child Cover"
    assert cover.unique_id == "eedomus_cover_cover_child"

    # 3. Vérification de la robustesse lors de la lecture des états (polling)
    assert cover.is_closed is True
    assert cover.current_cover_position == 0
    assert cover.current_cover_tilt_position is None

    # 4. Vérification de la robustesse lors de l'appel d'une action
    with patch.object(cover, "async_set_value") as mock_set_value:
        await cover.async_open_cover()
        mock_set_value.assert_called_once_with("100")
