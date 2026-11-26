"""
Configuration manager for Red Desktop Pet.
Handles configuration loading, schema validation, default fallbacks, and persistence.
"""

import json
from pathlib import Path
from typing import Any, Dict

DEFAULT_CONFIG: Dict[str, Any] = {
    "current_skin": "spine_red",
    "scale": 1.0,
    "dialogues_enabled": True,
    "companion_mode": {
        "activity_level": "quiet",   # "quiet", "gentle", "active"
        "dialogue_frequency": "rare"  # "rare", "normal", "off"
    }
}


class ConfigManager:
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self._config: Dict[str, Any] = self.load()

    def load(self) -> Dict[str, Any]:
        cfg = DEFAULT_CONFIG.copy()
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        cfg.update(data)
            except Exception as e:
                print(f"[ConfigManager] Error reading config file {self.config_path}: {e}")
        return cfg

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def set(self, key: str, value: Any, save: bool = True):
        self._config[key] = value
        if save:
            self.save()

    def save(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[ConfigManager] Error saving config file {self.config_path}: {e}")

    @property
    def data(self) -> Dict[str, Any]:
        return self._config
