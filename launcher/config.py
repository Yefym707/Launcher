"""Configuration loader and saver for the launcher."""

from pathlib import Path
from typing import List, Dict, Any

import yaml

DEFAULT_PANEL_POSITION = "top"

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"


def load_config(path: Path = CONFIG_PATH) -> List[Dict[str, Any]]:
    """Load section configuration from YAML file."""
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if "sections" in data:
        return data["sections"]
    if "items" in data:
        # backwards compatibility with older config format
        return [{"name": "Default", "items": data.get("items", [])}]
    return []


def load_panel_position(path: Path = CONFIG_PATH) -> str:
    """Return panel position stored in config file or the default."""
    if not path.exists():
        return DEFAULT_PANEL_POSITION
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    panel = data.get("panel", {})
    pos = str(panel.get("position", DEFAULT_PANEL_POSITION)).lower()
    if pos not in {"top", "bottom", "left", "right"}:
        pos = DEFAULT_PANEL_POSITION
    return pos


def save_config(sections: List[Dict[str, Any]], path: Path = CONFIG_PATH) -> None:
    """Save configuration back to YAML file while preserving other settings."""
    data = {}
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    data["sections"] = sections
    with path.open("w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True)
