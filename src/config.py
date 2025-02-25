import json
import os


def load_config(config_path="config.json"):
    """
    Load configuration settings from a JSON file.
    Defaults to 'config.json', but allows a custom path for testing.
    """
    if not os.path.exists(config_path):
        return {"dark_mode": False}  # Default config

    try:
        with open(config_path, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"dark_mode": False}


def save_config(config, config_path="config.json"):
    """
    Save configuration settings to a JSON file.
    Defaults to 'config.json', but allows a custom path for testing.
    """
    with open(config_path, "w") as file:
        json.dump(config, file, indent=4)
