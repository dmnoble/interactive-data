import os
import json
import pytest
from src.config import load_config, save_config, get_config_path

TEST_FILE = "test_config"


@pytest.fixture
def config_file():
    """Fixture to create/reset a temporary test config file before
    each test."""

    # Ensure the test config file starts fresh
    with open(get_config_path(TEST_FILE), "w") as f:
        json.dump({"dark_mode": True}, f)  # Reset to default

    yield TEST_FILE  # Provide the path for testing

    # Cleanup after test
    if os.path.exists(get_config_path(TEST_FILE)):
        os.remove(get_config_path(TEST_FILE))


def test_load_default_config(config_file):
    """Test loading default config from test file."""
    config = load_config(config_file)
    assert config == {"dark_mode": True}  # Ensure default is True


def test_save_and_load_config(config_file):
    """Test saving and reloading configuration settings."""
    test_config = {"dark_mode": False}
    save_config(test_config, config_file)

    loaded_config = load_config(config_file)
    assert loaded_config == test_config  # Ensure it saves correctly
