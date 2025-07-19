# tests/test_workspace_controller.py

import pytest
from unittest.mock import MagicMock
from src.workspace_controller import WorkspaceController
from PyQt5.QtCore import Qt, QAbstractTableModel


# Dummy concrete QAbstractTableModel subclass to pass type check
class DummyTableModel(QAbstractTableModel):
    def __init__(self):
        super().__init__()
        self._data: list[list[str]] = [
            ["Alice", "30"],
            ["Bob", "25"],
            ["Charlie", "35"],
        ]
        self._raw_data: list[dict[str, str]] = [
            {"name": "Alice", "age": "30"},
            {"name": "Bob", "age": "25"},
            {"name": "Charlie", "age": "35"},
        ]

        self._headers: list[str] = ["name", "age"]
        self.dark_mode: bool = False
        self._filter_expression = ""
        self._case_sensitive = False
        self._sort_key = ""

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self._headers)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and index.isValid():
            row = index.row()
            col = index.column()
            header = self._headers[col]
            return self._raw_data[row].get(header, "")
        return None

    def set_dark_mode(self, is_dark: bool) -> None:
        self.dark_mode = is_dark

    def is_dirty(self) -> bool:
        return False

    def is_backup_dirty(self) -> bool:
        return False

    def mark_backup_clean(self) -> None:
        pass

    def get_current_data_as_dicts(self):
        return [{"name": row[0], "age": row[1]} for row in self._data]

    def finalize_save(self):
        pass

    def undo(self):
        self._undo_called = True

    def redo(self):
        self._redo_called = True

    def was_undo_called(self):
        return self._undo_called


@pytest.fixture
def controller():
    return WorkspaceController()


def test_create_profile_new(monkeypatch, controller):
    # Patch profile list to simulate no existing profiles
    monkeypatch.setattr(controller, "get_profiles", lambda: [])
    monkeypatch.setattr(controller, "load_profile", lambda name: None)
    controller.data_manager.save_data = MagicMock()

    result = controller.create_profile("new_profile")

    assert result is True
    controller.data_manager.save_data.assert_called_with([], "new_profile")


def test_create_profile_existing(monkeypatch, controller):
    monkeypatch.setattr(
        controller, "get_profiles", lambda: ["existing_profile"]
    )

    result = controller.create_profile("existing_profile")

    assert result is False


def test_require_model_raises_without_model(controller):
    with pytest.raises(AssertionError, match="Model not loaded"):
        _ = controller.require_model


def test_set_model_binds_to_proxy(controller):
    model = DummyTableModel()
    controller.set_model(model)
    assert controller.model == model
    assert controller.proxy_model.sourceModel() == model


def test_undo_calls_model_undo(controller):
    model = DummyTableModel()
    controller.set_model(model)
    controller.undo()
    assert model.was_undo_called()


def test_redo_calls_model_redo(controller):
    model = DummyTableModel()
    controller.set_model(model)
    controller.redo()
    assert model._redo_called is True


def test_get_profiles_creates_config_dir(tmp_path, monkeypatch, controller):
    config_dir = tmp_path / "config_profiles"
    monkeypatch.setattr(controller, "CONFIG_DIR", config_dir)
    config_dir.mkdir(exist_ok=True)
    assert config_dir.exists()

    (config_dir / "user_config.json").write_text("{}")

    result = controller.get_profiles()
    assert "user" in result


def test_save_theme_to_config_sets_dark(controller):
    model = DummyTableModel()
    controller.profile_config = MagicMock()
    controller.set_model(model)

    controller.save_theme_to_config(True)

    controller.profile_config.set_theme.assert_called_with("Dark")
    assert model.dark_mode is True


def test_apply_custom_sort_assigns_values(controller):
    model = DummyTableModel()
    model._data = [["", ""], ["", ""]]

    controller.set_model(model)
    controller.proxy_model.sort_key_cache = {0: "zebra", 1: "apple"}

    result = controller.apply_custom_sort(
        controller.proxy_model.sort_key_cache
    )

    assert model._data[0][-1] == "zebra"
    assert model._data[1][-1] == "apple"
    assert "name" in result or "age" in result


def test_clear_custom_sort_resets_column(controller):
    model = DummyTableModel()
    model._headers.append(
        "sort_key"
    )  # Extend headers to reflect the new column
    for row in model._data:
        row.append("sort_value")  # Add a sort value in that column
    controller.set_model(model)

    controller.clear_custom_sort()

    for row in model._data:
        assert row[-1] == ""


def test_getters_return_view_config_values(controller):
    controller.view_config = {
        "custom_filter": "x > 5",
        "custom_sort_key": "length(name)",
        "case_sensitive": True,
        "ascending": False,
    }

    assert controller.get_custom_filter() == "x > 5"
    assert controller.get_custom_sort() == "length(name)"
    assert controller.get_filter_case_sensitive() is True
    assert controller.get_sort_order() is False
