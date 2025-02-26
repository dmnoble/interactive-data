import os
import json
import pytest
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
