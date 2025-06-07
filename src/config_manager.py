import json
from pathlib import Path
from typing import Optional

from logger import setup_logger


class ConfigManager:
    logger = setup_logger("config")

    DEFAULT_CONFIG = {
        "filters": {},
        "theme": "Light",
        "saved_views": [],
    }

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config = self._load()

    def _load(self) -> dict:
        if not self.config_path.exists():
            return self.DEFAULT_CONFIG.copy()
        try:
            with self.config_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            self.logger.warning(
                f"Corrupt JSON in {self.config_path}, using default config."
            )
            return self.DEFAULT_CONFIG.copy()

    def save(self) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with self.config_path.open("w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2)
            f.write("\n")

    # Theme management
    def get_theme(self) -> str:
        return self.config.get("theme", self.DEFAULT_CONFIG["theme"])

    def set_theme(self, theme: str) -> None:
        self.config["theme"] = theme
        self.save()

    def is_dark_mode(self) -> bool:
        return self.get_theme().lower() == "dark"

    # Saved Views management
    def get_saved_views(self) -> list[dict]:
        return self.config.get("saved_views", [])

    def save_view(self, view_config: dict) -> None:
        views = [
            v
            for v in self.get_saved_views()
            if v.get("name") != view_config.get("name")
        ]
        views.append(view_config)
        self.config["saved_views"] = views
        self.save()

    def delete_view(self, name: str) -> None:
        views = [v for v in self.get_saved_views() if v.get("name") != name]
        self.config["saved_views"] = views
        self.save()

    def get_view_by_name(self, name: str) -> Optional[dict]:
        return next(
            (v for v in self.get_saved_views() if v.get("name") == name), None
        )

    def get_default_view(self) -> Optional[dict]:
        return next(
            (v for v in self.get_saved_views() if v.get("default")), None
        )
