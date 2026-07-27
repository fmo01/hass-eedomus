#!/usr/bin/env python3
"""
Eedomus Table Generation Script
Generates a device mapping table and JSON data from the eedomus API.
Uses exact YAML loading, merging, and priority logic from the integration modules.
"""

import os
import sys
import json
import logging
import re
import urllib.request
import urllib.error
import yaml

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
_LOGGER = logging.getLogger(__name__)

# Credentials
EEDOMUS_API_HOST = os.getenv("EEDOMUS_API_HOST", "192.168.1.10")
EEDOMUS_API_USER = os.getenv("EEDOMUS_API_USER", "")
EEDOMUS_API_SECRET = os.getenv("EEDOMUS_API_SECRET", "")

# Dossier des configurations YAML (paramétrable via variable d'environnement)
CONFIG_DIR = os.getenv("EEDOMUS_CONFIG_DIR", "config")

# Output Files
MD_FILE = "simple_device_table.md"
JSON_FILE = "simple_device_data.json"

# Input YAML Files (dynamically resolved using the configured directory)
DEFAULT_MAPPING_FILE = os.path.join(CONFIG_DIR, "device_mapping.yaml")
CUSTOM_MAPPING_FILE = os.path.join(CONFIG_DIR, "custom_mapping.yaml")

# ---------------------------------------------------------------------------
# YAML LOADING & MERGING LOGIC
# ---------------------------------------------------------------------------
def load_yaml_file(file_path):
    """Load YAML configuration from file."""
    try:
        if not os.path.exists(file_path):
            _LOGGER.warning(f"File not found: {file_path}")
            return {}
            
        with open(file_path, "r", encoding="utf-8") as file:
            content = yaml.safe_load(file)
            if content:
                # Convert list format to dict format if needed
                if isinstance(content, list):
                    return {
                        "advanced_rules": content,
                        "usage_id_mappings": {},
                        "name_patterns": [],
                        "dynamic_entity_properties": {},
                        "specific_device_dynamic_overrides": {},
                    }
                return content
            return {}
    except Exception as e:
        _LOGGER.error(f"Failed to parse YAML file {file_path}: {e}")
        return {}

def merge_yaml_mappings(default_mapping, custom_mapping):
    """Merge default and custom mappings, with custom mappings taking precedence."""
    merged = {}

    # Merge usage ID mappings
    merged["usage_id_mappings"] = default_mapping.get("usage_id_mappings", {})
    if "custom_usage_id_mappings" in custom_mapping and isinstance(custom_mapping["custom_usage_id_mappings"], dict):
        merged["usage_id_mappings"].update(custom_mapping["custom_usage_id_mappings"])

    # Merge name patterns
    merged["name_patterns"] = default_mapping.get("name_patterns", [])
    if "custom_name_patterns" in custom_mapping and isinstance(custom_mapping["custom_name_patterns"], list):
        merged["name_patterns"].extend(custom_mapping["custom_name_patterns"])

    # Merge specific device dynamic overrides
    merged["specific_device_dynamic_overrides"] = default_mapping.get("specific_device_dynamic_overrides", {})
    if "custom_specific_device_dynamic_overrides" in custom_mapping and isinstance(custom_mapping["custom_specific_device_dynamic_overrides"], dict):
        merged["specific_device_dynamic_overrides"].update(custom_mapping["custom_specific_device_dynamic_overrides"])

    # Add default mapping
    merged["default_mapping"] = default_mapping.get("default_mapping", {
        "ha_entity": "sensor",
        "ha_subtype": "unknown",
        "justification": "Fallback default mapping"
    })

    return merged

def load_and_merge_mappings():
    """Load and merge YAML mappings from default and custom files."""
    _LOGGER.info(f"Target configuration directory: {os.path.abspath(CONFIG_DIR)}")
    
    _LOGGER.info(f"Loading default mapping from {DEFAULT_MAPPING_FILE}...")
    default_mapping = load_yaml_file(DEFAULT_MAPPING_FILE)
    
    _LOGGER.info(f"Loading custom mapping from {CUSTOM_MAPPING_FILE}...")
    custom_mapping = load_yaml_file(CUSTOM_MAPPING_FILE)
    
    _LOGGER.info("Merging mappings...")
    return merge_yaml_mappings(default_mapping, custom_mapping)

# Initialize global mapping
DEVICE_MAPPINGS = load_and_merge_mappings()

# ---------------------------------------------------------------------------
# MAPPING RESOLUTION LOGIC
# ---------------------------------------------------------------------------
def get_ha_mapping(device_data):
    """
    Core device mapping function using priority-based approach.
    Determines HA entity string (ha_entity:ha_subtype).
    """
    periph_id = str(device_data.get("periph_id", ""))
    usage_id = str(device_data.get("usage_id", ""))
    name = device_data.get("name", "")
    name_lower = name.lower()

    # Priority 1: Specific critical cases (usage_id-based)
    specific_cases = {
        "27": ("binary_sensor", "smoke"),
        "37": ("binary_sensor", "motion"),
    }
    if usage_id in specific_cases:
        ha_entity, ha_subtype = specific_cases[usage_id]
        return f"{ha_entity}:{ha_subtype}"

    # Priority 2: Specific device dynamic overrides by periph_id
    if periph_id in DEVICE_MAPPINGS.get("specific_device_dynamic_overrides", {}):
        mapping = DEVICE_MAPPINGS["specific_device_dynamic_overrides"][periph_id]
        return f"{mapping.get('ha_entity', 'unknown')}:{mapping.get('ha_subtype', 'unknown')}"

    # Priority 3: Usage ID mapping
    if usage_id in DEVICE_MAPPINGS.get("usage_id_mappings", {}):
        mapping = DEVICE_MAPPINGS["usage_id_mappings"][usage_id]
        return f"{mapping.get('ha_entity', 'unknown')}:{mapping.get('ha_subtype', 'unknown')}"

    # Priority 4: Name pattern matching
    for pattern in DEVICE_MAPPINGS.get("name_patterns", []):
        if "pattern" in pattern and re.search(pattern["pattern"], name_lower, re.IGNORECASE):
            return f"{pattern.get('ha_entity', 'unknown')}:{pattern.get('ha_subtype', 'unknown')}"
            
    # Legacy specific string matching
    if "message" in name_lower and "box" in name_lower:
        return "sensor:text"

    # Priority 5: Default mapping
    default_config = DEVICE_MAPPINGS.get("default_mapping", {})
    ha_entity = default_config.get("ha_entity", "sensor")
    ha_subtype = default_config.get("ha_subtype", "unknown")
    
    return f"{ha_entity}:{ha_subtype}"

def clean_zwave_classes(raw_classes):
    """Simplifies Z-Wave classes to base numbers only."""
    if not raw_classes:
        return "N/A"
    numbers = re.findall(r'\b\d+\b', str(raw_classes))
    if numbers:
        return ", ".join(numbers)
    return str(raw_classes)

# ---------------------------------------------------------------------------
# API AND GENERATION
# ---------------------------------------------------------------------------
def fetch_eedomus_data():
    """Connects to eedomus API using standard urllib."""
    if not EEDOMUS_API_USER or not EEDOMUS_API_SECRET:
        _LOGGER.error("API credentials missing. Set EEDOMUS_API_USER and EEDOMUS_API_SECRET.")
        sys.exit(1)

    # Corrected API endpoint
    url = f"http://{EEDOMUS_API_HOST}/api/get?api_user={EEDOMUS_API_USER}&api_secret={EEDOMUS_API_SECRET}&action=periph.list"
    _LOGGER.info(f"Fetching data from eedomus box at {EEDOMUS_API_HOST}...")
    
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as response:
            raw_data = response.read()
            try:
                decoded_data = raw_data.decode('utf-8')
            except UnicodeDecodeError:
                decoded_data = raw_data.decode('iso-8859-1')
                
            json_data = json.loads(decoded_data)
            if json_data.get("success") != 1:
                _LOGGER.error(f"API returned an error: {json_data}")
                sys.exit(1)
            return json_data.get("body", [])
            
    except Exception as err:
        _LOGGER.error(f"Failed to connect to eedomus API or parse data: {err}")
        sys.exit(1)

def generate_outputs(devices):
    """Process device data and generate Markdown and JSON files."""
    processed_data = []
    sorted_devices = sorted(devices, key=lambda x: str(x.get("periph_id", "")))
    _LOGGER.info(f"Processing {len(sorted_devices)} devices...")

    for dev in sorted_devices:
        periph_id = dev.get("periph_id", "N/A")
        parent_id = dev.get("parent_periph_id", "")
        usage_id = dev.get("usage_id", "N/A")
        usage_name = dev.get("usage_name", "N/A")
        name = dev.get("name", "N/A")
        room = dev.get("room_name", "N/A")
        
        raw_classes = dev.get("zwave_class", "") or dev.get("supported_classes", "")
        clean_classes = clean_zwave_classes(raw_classes)
        
        ha_mapping = get_ha_mapping(dev)
        
        parent_periph_combo = f"{parent_id}/{periph_id}" if parent_id else f"-/{periph_id}"
        usage_combo = f"{usage_id}:{usage_name}"
        
        processed_data.append({
            "raw": dev,
            "table_row": [parent_periph_combo, usage_combo, clean_classes, ha_mapping, name, room]
        })

    _LOGGER.info(f"Generating Markdown file: {MD_FILE}")
    with open(MD_FILE, 'w', encoding='utf-8') as md:
        md.write("# Eedomus Simple Device Table\n\n")
        md.write("Generated automatically from eedomus API using modular mapping logic.\n\n")
        md.write("| parent_id/periph_id | usage_id:usage_name | SUPPORTED_CLASSES | ha_type:ha_subtype | name | room |\n")
        md.write("|---------------------|---------------------|-------------------|--------------------|------|------|\n")
        for item in processed_data:
            row = item["table_row"]
            md.write(f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} |\n")

    _LOGGER.info(f"Generating JSON file: {JSON_FILE}")
    json_output = [item["raw"] for item in processed_data]
    with open(JSON_FILE, 'w', encoding='utf-8') as jf:
        json.dump(json_output, jf, indent=4, ensure_ascii=False)

    _LOGGER.info("Generation complete!")

# ---------------------------------------------------------------------------
# MAIN EXECUTION
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    _LOGGER.info("Starting eedomus table generation script...")
    raw_devices = fetch_eedomus_data()
    generate_outputs(raw_devices)
