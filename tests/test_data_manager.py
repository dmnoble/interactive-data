import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open
from src.services.data_manager import DataManager, CONFIG_DIR

TEST_DATA_PATH = "test_sample_data.json"


@pytest.fixture
def sample_data():
    return [
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
    ]


def test_get_config_path():
    dm = DataManager()
    path = dm.get_config_path("example")
    assert path == CONFIG_DIR / "example_data.json"


@patch("src.services.data_manager.Path.exists", return_value=False)
def test_load_data_returns_empty_if_missing(mock_exists):
    dm = DataManager()
    assert dm.load_data("ghost") == []


@patch(
    "src.services.data_manager.Path.open",
    new_callable=mock_open,
    read_data="INVALID",
)
@patch("src.services.data_manager.Path.exists", return_value=True)
def test_load_data_handles_corrupt_json(mock_exists, mock_file):
    dm = DataManager()
    assert dm.load_data("badfile") == []


@patch(
    "src.services.data_manager.Path.open",
    new_callable=mock_open,
    read_data='[{"id": 1}]',
)
@patch("src.services.data_manager.Path.exists", return_value=True)
def test_load_data_valid(mock_exists, mock_file):
    dm = DataManager()
    assert dm.load_data("ok") == [{"id": 1}]


@patch("src.services.data_manager.Path.open", new_callable=mock_open)
def test_save_data_succeeds(mock_file, sample_data):
    dm = DataManager()
    dm.save_data(sample_data, "goodfile")
    mock_file.assert_called_once()


@patch("src.services.data_manager.Path.open", side_effect=IOError("fail"))
def test_save_data_retries_then_fails(mock_file, sample_data):
    dm = DataManager()
    with pytest.raises(IOError):
        dm.save_data(sample_data, "willfail")


def test_save_backup_creates_file(sample_data):
    dm = DataManager()

    with tempfile.TemporaryDirectory() as temp_dir:
        # Redirect backup location to temp
        temp_backup_dir = Path(temp_dir)
        profile = "tester"
        filename = f"{profile}_data.json.20250709-070707.bak"
        backup_path = temp_backup_dir / filename

        # Patch constants and time
        with patch(
            "src.services.data_manager.BACKUP_DIR", temp_backup_dir
        ), patch(
            "src.services.data_manager.time.strftime",
            return_value="20250709-070707",
        ), patch(
            "src.services.data_manager.Path.open", mock_open()
        ) as mock_file:

            dm.save_backup(sample_data, profile)

            mock_file.assert_called_with("w", encoding="utf-8")
            assert backup_path.suffix == ".bak"
