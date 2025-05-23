import json
import os
from logger import setup_logger


class ConfigManager:
    logger = setup_logger("config")

    DEFAULT_CONFIG = {"dark_mode": True, "filters": {}}

    def __init__(self, config_path):
        self.config_path = config_path
        self.config = self._load()

    def _load(self):
        if not os.path.exists(self.config_path):
            return self.DEFAULT_CONFIG
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return self.DEFAULT_CONFIG

    def save(self):
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2)

    # Theme management
    def get_theme(self):
        return self.config.get("theme", "Light")

    def set_theme(self, theme):
        self.config["theme"] = theme
        self.save()

    def is_dark_mode(self):
        return self.get_theme().lower() == "dark"

    # Saved Views management
    def get_saved_views(self):
        return self.config.get("saved_views", [])

    def save_view(self, view_config):
        views = self.get_saved_views()
        views = [v for v in views if v.get("name") != view_config.get("name")]
        views.append(view_config)
        self.config["saved_views"] = views
        self.save()

    def delete_view(self, name):
        views = [v for v in self.get_saved_views() if v.get("name") != name]
        self.config["saved_views"] = views
        self.save()

    def get_view_by_name(self, name):
        return next(
            (v for v in self.get_saved_views() if v.get("name") == name), None
        )

    def get_default_view(self):
        for view in self.get_saved_views():
            if view.get("default"):
                return view
        return None
