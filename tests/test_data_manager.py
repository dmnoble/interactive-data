import os
import json
import pytest
from src.data_manager import load_data, save_data

TEST_DATA_PATH = "test_data.json"


@pytest.fixture
def data_file():
    """Fixture to create/reset a temporary test config file before
    each test."""

    # Ensure the test config file starts fresh
    with open(TEST_DATA_PATH, "w") as f:
        json.dump({"dark_mode": False}, f)  # Reset to default

    yield TEST_DATA_PATH  # Provide the path for testing

    # Cleanup after test
    if os.path.exists(TEST_DATA_PATH):
        os.remove(TEST_DATA_PATH)


def test_load_default_config(config_file):
    """Test loading default config when file exists but should contain
    defaults."""
    config = load_data(config_file)
    assert config == {"dark_mode": False}  # Ensure default is False


def test_save_and_load_config(config_file):
    """Test saving and reloading configuration settings."""
    test_config = {"dark_mode": True}
    save_data(test_config, config_file)

    loaded_config = load_data(config_file)
    assert loaded_config == test_config  # Ensure it saves correctly
