import json
import os
from logger import setup_logger

logger = setup_logger("config")

CONFIG_DIR = "config_profiles"  # Directory to store user configs
DEFAULT_CONFIG = {"dark_mode": True, "filters": {}}
CONFIG_END = "_config.json"


def get_profiles():
    """Returns a list of available profiles based on config files."""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
    return [
        f.replace(CONFIG_END, "")
        for f in os.listdir(CONFIG_DIR)
        if f.endswith(CONFIG_END)
    ]


def get_config_path(profilename):
    """Returns the config file path for a specific profile."""
    return os.path.join(CONFIG_DIR, f"{profilename}{CONFIG_END}")


def load_config(profilename="default"):
    """
    Loads the user's configuration settings from a JSON file, or returns
    defaults if not found.
    """
    config_path = get_config_path(profilename)

    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)  # Create directory if missing

    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            logger.exception(f"Config: could not find {config_path}.")
            return DEFAULT_CONFIG
    return DEFAULT_CONFIG


def save_config(config, profilename="default"):
    """Saves the user's config settings."""
    config_path = get_config_path(profilename)

    with open(config_path, "w") as file:
        json.dump(config, file, indent=4)
