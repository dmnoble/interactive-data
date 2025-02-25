import os
import json
import pytest
from src.config import load_config, save_config

TEST_CONFIG_PATH = "test_config.json"


@pytest.fixture
def config_file():
    """Fixture to create/reset a temporary test config file before
    each test."""

    # Ensure the test config file starts fresh
    with open(TEST_CONFIG_PATH, "w") as f:
        json.dump({"dark_mode": False}, f)  # Reset to default

    yield TEST_CONFIG_PATH  # Provide the path for testing

    # Cleanup after test
    if os.path.exists(TEST_CONFIG_PATH):
        os.remove(TEST_CONFIG_PATH)


def test_load_default_config(config_file):
    """Test loading default config from test file."""
    config = load_config(config_file)
    assert config == {"dark_mode": False}  # Ensure default is False


def test_save_and_load_config(config_file):
    """Test saving and reloading configuration settings."""
    test_config = {"dark_mode": True}
    save_config(test_config, config_file)

    loaded_config = load_config(config_file)
    assert loaded_config == test_config  # Ensure it saves correctly
