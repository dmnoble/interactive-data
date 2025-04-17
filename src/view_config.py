import json
from pathlib import Path

VIEWS_FILE = Path("saved_views.json")


def load_all_views():
    if VIEWS_FILE.exists():
        with open(VIEWS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_view_config(name, config):
    views = load_all_views()
    views[name] = config
    with open(VIEWS_FILE, "w", encoding="utf-8") as f:
        json.dump(views, f, indent=2)


def get_view_config(name):
    return load_all_views().get(name)


def get_all_view_names():
    return list(load_all_views().keys())
