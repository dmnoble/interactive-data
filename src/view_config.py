import json
import os
from pathlib import Path

CONFIG_DIR = "config_profiles"
VIEWS_END = "_views.json"


def get_config_path(profilename):
    """Returns the config file path for a specific profile."""
    return os.path.join(CONFIG_DIR, f"{profilename}{VIEWS_END}")


def load_all_views(profilename="default"):
    config_path = get_config_path(profilename)
    if Path(config_path).exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_view_config(name, config, profilename="default"):
    config_path = get_config_path(profilename)
    views = load_all_views(profilename)
    views[name] = config
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(views, f, indent=2)


def get_view_config(name, profilename="default"):
    return load_all_views(profilename).get(name)


def get_all_view_names(profilename="default"):
    return list(load_all_views(profilename).keys())


def get_default_view_name(profilename="default"):
    views = load_all_views(profilename)
    for name, config in views.items():
        if config.get("default"):
            return name
    return None


def set_default_view(name, profilename="default"):
    config_path = get_config_path(profilename)
    views = load_all_views()
    for vname in views:
        views[vname]["default"] = views[vname]["default"] = vname == name
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(views, f, indent=2)
