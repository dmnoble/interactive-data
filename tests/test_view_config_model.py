import tempfile
from pathlib import Path
import pytest

import src.models.view_config_model as vc


@pytest.fixture
def temp_config_dir(monkeypatch):
    with tempfile.TemporaryDirectory() as tempdir:
        monkeypatch.setattr(vc, "CONFIG_DIR", Path(tempdir))
        yield Path(tempdir)


def test_save_and_get_view_config(temp_config_dir):
    profile = "testprofile"
    view_name = "testview"
    config = {"filter_expr": "x > 5", "default": True}

    vc.save_view_config(view_name, config, profile)
    loaded = vc.get_view_config(view_name, profile)

    assert loaded == config


def test_get_all_view_names(temp_config_dir):
    profile = "testprofile"
    vc.save_view_config("v1", {"dummy": 1}, profile)
    vc.save_view_config("v2", {"dummy": 2}, profile)

    names = vc.get_all_view_names(profile)
    assert set(names) == {"v1", "v2"}


def test_set_and_get_default_view(temp_config_dir):
    profile = "testprofile"
    vc.save_view_config("v1", {"default": False}, profile)
    vc.save_view_config("v2", {"default": False}, profile)

    vc.set_default_view("v2", profile)
    default_view = vc.get_default_view_name(profile)

    assert default_view == "v2"


def test_delete_view(temp_config_dir):
    profile = "testprofile"
    vc.save_view_config("v1", {"some": "thing"}, profile)
    assert vc.get_view_config("v1", profile) is not None

    vc.delete_view("v1", profile)
    assert vc.get_view_config("v1", profile) is None


# 💡 New Tests


def test_get_view_config_returns_none_for_missing_view(temp_config_dir):
    profile = "testprofile"
    vc.save_view_config("existing", {"some": "value"}, profile)

    result = vc.get_view_config("nonexistent", profile)
    assert result is None


def test_get_default_view_name_returns_none_if_none_set(temp_config_dir):
    profile = "testprofile"
    vc.save_view_config("v1", {"default": False}, profile)
    vc.save_view_config("v2", {"default": False}, profile)

    result = vc.get_default_view_name(profile)
    assert result is None


def test_delete_view_silent_if_view_missing(temp_config_dir):
    profile = "testprofile"
    # Deleting nonexistent view should not crash
    vc.delete_view("ghost", profile)  # should pass silently
