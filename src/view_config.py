import json
from pathlib import Path
from typing import Optional

CONFIG_DIR = Path("config_profiles")
VIEWS_SUFFIX = "_views.json"


def get_config_path(profile_name: str) -> Path:
    """Return the view config path for a profile."""
    return CONFIG_DIR / f"{profile_name}{VIEWS_SUFFIX}"


def load_all_views(profile_name: str = "default") -> dict:
    """Load all saved views for a profile."""
    config_path = get_config_path(profile_name)
    if config_path.exists():
        with config_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_view_config(
    view_name: str, config: dict, profile_name: str = "default"
) -> None:
    """Save a view configuration under the given name."""
    views = load_all_views(profile_name)
    views[view_name] = config
    config_path = get_config_path(profile_name)
    with config_path.open("w", encoding="utf-8") as f:
        json.dump(views, f, indent=2)


def get_view_config(
    view_name: str, profile_name: str = "default"
) -> Optional[dict]:
    """Retrieve a specific view configuration."""
    return load_all_views(profile_name).get(view_name)


def get_all_view_names(profile_name: str = "default") -> list[str]:
    """Return a list of saved view names for a profile."""
    return list(load_all_views(profile_name).keys())


def get_default_view_name(profile_name: str = "default") -> Optional[str]:
    """Return the default view name if one is marked as such."""
    views = load_all_views(profile_name)
    for name, config in views.items():
        if config.get("default"):
            return name
    return None


def set_default_view(view_name: str, profile_name: str = "default") -> None:
    """Mark one view as the default and unmark others."""
    views = load_all_views(profile_name)
    for name in views:
        views[name]["default"] = name == view_name

    config_path = get_config_path(profile_name)
    with config_path.open("w", encoding="utf-8") as f:
        json.dump(views, f, indent=2)
