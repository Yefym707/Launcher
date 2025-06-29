"""Configuration loader and saver for the launcher."""

from pathlib import Path
from typing import List, Dict, Any

import yaml

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"


def load_config(path: Path = CONFIG_PATH) -> List[Dict[str, Any]]:
    """Load configuration from YAML file."""
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


def save_config(sections: List[Dict[str, Any]], path: Path = CONFIG_PATH) -> None:
    """Save configuration back to YAML file."""
    with path.open("w", encoding="utf-8") as f:
        yaml.dump({"sections": sections}, f, allow_unicode=True)
