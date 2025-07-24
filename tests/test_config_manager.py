"""
Pytest version of tests for src.config_manager.ConfigManager
"""

from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from src.services.config_manager import ConfigManager


# ---------- fixtures ------------------------------------------------------- #


@pytest.fixture
def default_config():
    """Canonical default config used across tests."""
    return {"filters": {}, "theme": "Light", "saved_views": []}


@pytest.fixture
def mock_config_path(tmp_path: Path) -> Path:
    """Path inside pytest’s tmp directory, so nothing touches the real FS."""
    return tmp_path / "mock_config.json"


# ---------- tests ---------------------------------------------------------- #


def test_load_returns_default_if_file_missing(
    mock_config_path, default_config
):
    with patch("src.services.config_manager.Path.exists", return_value=False):
        cm = ConfigManager(mock_config_path)
    assert cm.config == default_config


def test_load_corrupt_json_returns_default(mock_config_path, default_config):
    m_open = mock_open(read_data="INVALID JSON")
    with patch(
        "src.services.config_manager.Path.exists", return_value=True
    ), patch("src.services.config_manager.Path.open", m_open):
        cm = ConfigManager(mock_config_path)

    assert cm.config == default_config


def test_save_writes_file(mock_config_path):
    m_open = mock_open()
    # First instantiation should *not* find the file
    with patch(
        "src.services.config_manager.Path.exists", return_value=False
    ), patch("src.services.config_manager.Path.open", m_open):
        cm = ConfigManager(mock_config_path)
        cm.save()

    m_open.assert_called_with("w", encoding="utf-8")


def test_get_and_set_theme(mock_config_path):
    cm = ConfigManager(mock_config_path)
    cm.set_theme("Dark")
    assert cm.get_theme() == "Dark"


@pytest.mark.parametrize("theme, expected", [("Dark", True), ("Light", False)])
def test_is_dark_mode(theme, expected, mock_config_path):
    cm = ConfigManager(mock_config_path)
    cm.set_theme(theme)
    assert cm.is_dark_mode() is expected


def test_save_and_get_view(mock_config_path):
    cm = ConfigManager(mock_config_path)
    cm.save_view({"name": "TestView", "default": True})

    assert len(cm.get_saved_views()) == 1
    assert cm.get_view_by_name("TestView") == {
        "name": "TestView",
        "default": True,
    }


def test_delete_view(mock_config_path):
    cm = ConfigManager(mock_config_path)
    cm.save_view({"name": "ToDelete"})
    cm.delete_view("ToDelete")

    assert cm.get_saved_views() == []


def test_get_default_view(mock_config_path):
    cm = ConfigManager(mock_config_path)
    cm.save_view({"name": "v1"})
    cm.save_view({"name": "v2", "default": True})

    assert cm.get_default_view() == {"name": "v2", "default": True}
