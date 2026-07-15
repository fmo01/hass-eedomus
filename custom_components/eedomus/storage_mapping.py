"""The eedomus integration."""

from __future__ import annotations

import logging
import os

import voluptuous as vol

# Initialize logger first
_LOGGER = logging.getLogger(__name__)

# YAML Mapping Management Functions


async def async_load_mapping(hass, config_dir):
    """Load and merge device mappings from YAML files.

    This function loads default and custom device mappings from YAML files,
    merges them using a sophisticated algorithm, and validates the result.
    """
    import yaml

    from .const import YAML_MAPPING_SCHEMA

    default_path = os.path.join(config_dir, "device_mapping.yaml")
    custom_path = os.path.join(config_dir, "custom_mapping.yaml")

    # Load default mapping using async executor to avoid blocking event loop
    default_mapping = {}
    try:
        default_path = os.path.join(
            os.path.dirname(__file__), "config", "device_mapping.yaml"
        )
        default_mapping = await hass.async_add_executor_job(
            lambda: yaml.safe_load(open(default_path, "r", encoding="utf-8")) or {}
        )
        _LOGGER.debug("Loaded default mapping from %s", default_path)
    except FileNotFoundError:
        _LOGGER.warning("Default mapping file not found: %s", default_path)
    except yaml.YAMLError as e:
        _LOGGER.error("Error parsing default mapping YAML: %s", e)
        raise
    except Exception as e:
        _LOGGER.error("Unexpected error loading default mapping: %s", e)
        raise

    # Load custom mapping using async executor to avoid blocking event loop
    custom_mapping = {}
    try:
        custom_path = os.path.join(
            os.path.dirname(__file__), "config", "custom_mapping.yaml"
        )
        custom_mapping = await hass.async_add_executor_job(
            lambda: yaml.safe_load(open(custom_path, "r", encoding="utf-8")) or {}
        )
        _LOGGER.debug("Loaded custom mapping from %s", custom_path)
    except FileNotFoundError:
        _LOGGER.debug(
            "No custom mapping file found at %s - using defaults only", custom_path
        )
    except yaml.YAMLError as e:
        _LOGGER.error("Error parsing custom mapping YAML: %s", e)
        raise
    except Exception as e:
        _LOGGER.error("Unexpected error loading custom mapping: %s", e)
        raise

    # Merge mappings using sophisticated approach (same as load_and_merge_yaml_mappings)
    # This ensures proper handling of nested structures like lists and dictionaries
    try:
        from .device_mapping import merge_yaml_mappings

        merged = merge_yaml_mappings(default_mapping, custom_mapping)
        _LOGGER.debug("Mappings merged successfully using sophisticated merge")
    except Exception as e:
        _LOGGER.error("Sophisticated merge failed, falling back to simple merge: %s", e)
        # Fallback to simple merge if sophisticated merge fails
        merged = {**default_mapping, **custom_mapping}

    # Validate merged mapping
    try:
        validated = YAML_MAPPING_SCHEMA(merged)
        _LOGGER.debug("Mapping validation successful")
        return validated
    except vol.Invalid as e:
        _LOGGER.error("Mapping validation failed: %s", e)
        raise


async def async_save_custom_mapping(hass, config_dir, mapping_data):
    """Save custom mapping to YAML file.

    This function saves custom device mapping data to a YAML file for persistent
    storage across Home Assistant restarts.
    """
    import yaml

    custom_path = os.path.join(config_dir, "custom_mapping.yaml")

    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(custom_path), exist_ok=True)

        with open(custom_path, "w", encoding="utf-8") as f:
            yaml.dump(
                mapping_data,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )
            _LOGGER.info("Custom mapping saved to %s", custom_path)
            return True
    except Exception as e:
        _LOGGER.error("Failed to save custom mapping: %s", e)
        return False
