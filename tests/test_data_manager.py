import os
import json
import pytest
import tempfile
from unittest.mock import patch, mock_open
from src.data_manager import DataManager

TEST_DATA_PATH = "test_sample_data.json"


@pytest.fixture
def test_data_manager():
    """Fixture to create a temporary DataManager instance with sample data."""

    # Sample test data
    sample_data = [
        {
            "id": 1,
            "name": "Alice",
            "age": 30,
            "email": "alice@example.com",
            "last_accessed": "2023-11-15",
            "tags": ["admin", "verified"],
            "preferences": {"theme": "dark", "notifications": True},
        },
        {
            "id": 2,
            "name": "Bob",
            "age": 25,
            "email": "bob@example.com",
            "last_accessed": "2024-02-10",
            "tags": ["user"],
            "preferences": {"theme": "light", "notifications": False},
        },
        {
            "id": 3,
            "name": "Charlie",
            "age": 35,
            "email": "charlie@example.com",
            "last_accessed": "2023-08-05",
            "tags": ["moderator", "premium"],
            "preferences": {"theme": "dark", "notifications": True},
        },
    ]

    # Ensure the test file starts fresh
    with open(TEST_DATA_PATH, "w") as f:
        json.dump(sample_data, f)  # Reset to default

    dm = DataManager(TEST_DATA_PATH)  # Load DataManager with sample file
    yield dm  # Provide instance to tests

    # Cleanup after test
    if os.path.exists(TEST_DATA_PATH):
        os.remove(TEST_DATA_PATH)


def test_load_sample_data(test_data_manager):
    """Test loading sample data."""
    data = test_data_manager.load_data()
    assert len(data) == 3  # Ensure we have 3 records
    assert data[0]["name"] == "Alice"  # Check first user
    assert data[1]["tags"] == ["user"]  # Check Bob's tags
    assert data[2]["preferences"]["theme"] == "dark"  # Check preferences


def test_save_and_load_data_roundtrip():
    # Create a temp file to avoid writing to real data
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
        temp_path = tmp.name

    try:
        manager = DataManager(temp_path)
        test_data = [
            {"name": "Alice", "role": "Engineer", "status": "Active"},
            {"name": "Bob", "role": "Designer", "status": "Inactive"},
        ]

        manager.save_data(test_data)

        # Ensure file was created
        assert os.path.exists(temp_path), "Save file was not created"

        # Read it back and compare
        with open(temp_path, "r") as f:
            loaded = json.load(f)

        assert loaded == test_data, "Saved data does not match input"

    finally:
        os.remove(temp_path)


def test_save_data_with_unicode_characters():
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=".json", mode="w+", encoding="utf-8"
    ) as tmp:
        temp_path = tmp.name

    try:
        manager = DataManager(temp_path)
        test_data = [
            {"name": "Zoë 🌟", "role": "Développeuse", "status": "✔️ Active"},
            {"name": "李雷", "role": "设计师", "status": "🚧 Inactive"},
        ]

        manager.save_data(test_data)

        # Reload and verify contents
        with open(temp_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)

        assert (
            loaded == test_data
        ), "Unicode data did not match after save/load"

    finally:
        os.remove(temp_path)


def test_save_data_raises_ioerror():
    manager = DataManager("fake_path.json")
    test_data = [{"name": "Error Case"}]

    with patch("builtins.open", mock_open()) as mocked_open:
        mocked_open.side_effect = IOError("Disk full or write protected")

        try:
            manager.save_data(test_data)
            assert False, "Expected IOError was not raised"
        except IOError as e:
            assert "Disk full" in str(e) or "write protected" in str(e)
