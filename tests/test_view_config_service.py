import pytest
from pathlib import Path
from src.view_config_service import ViewConfigService


@pytest.fixture
def sample_view_config():
    return {"columns": ["name", "age"], "sort": "name"}


@pytest.fixture
def profile_name():
    return "test_profile"


@pytest.fixture(autouse=True)
def delete_test_profile_json():
    yield
    (Path.cwd() / "config_profiles" / "test_profile_views.json").unlink(
        missing_ok=True
    )


def test_save_and_load_view(sample_view_config, profile_name):
    ViewConfigService.save_view("test_view", sample_view_config, profile_name)
    loaded = ViewConfigService.load_view("test_view", profile_name)
    assert loaded == sample_view_config


def test_get_all_view_names(sample_view_config, profile_name):
    ViewConfigService.save_view("test_view", sample_view_config, profile_name)
    names = ViewConfigService.list_views(profile_name)
    assert "test_view" in names


def test_set_and_get_default_view(sample_view_config, profile_name):
    ViewConfigService.save_view(
        "default_view", sample_view_config, profile_name
    )
    ViewConfigService.set_default("default_view", profile_name)
    assert ViewConfigService.get_default(profile_name) == "default_view"


def test_set_default_view_does_nothing_if_invalid(profile_name):
    ViewConfigService.set_default("nonexistent", profile_name)
    assert ViewConfigService.get_default(profile_name) is None


def test_get_view_not_found_returns_none(profile_name):
    assert ViewConfigService.load_view("missing_view", profile_name) is None


def test_multiple_views_default_assignment(sample_view_config, profile_name):
    ViewConfigService.save_view("view1", sample_view_config, profile_name)
    ViewConfigService.save_view("view2", sample_view_config, profile_name)
    ViewConfigService.set_default("view2", profile_name)

    assert ViewConfigService.get_default(profile_name) == "view2"
    assert "view1" in ViewConfigService.list_views(profile_name)
    assert "view2" in ViewConfigService.list_views(profile_name)
