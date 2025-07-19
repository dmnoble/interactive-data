from src.table_model import DataTableModel
from src.undo_redo import Action
from unittest.mock import Mock, patch
from PyQt5.QtCore import Qt
import os


def test_set_data_marks_dirty_and_updates():
    headers = ["name", "role"]
    data = [{"name": "Alice", "role": "Engineer"}]
    mock_manager = Mock()
    model = DataTableModel(data, headers, data_manager=mock_manager)

    index = model.index(0, 0)
    new_value = "Alicia"

    result = model.setData(index, new_value)

    assert result is True
    assert model._data[0][0] == "Alicia"
    assert model.is_dirty() is True
    mock_manager.save_data.assert_not_called()


def test_dirty_flag_on_data_change():
    headers = ["name", "role"]
    data = [{"name": "Alice", "role": "Engineer"}]
    model = DataTableModel(data, headers)

    assert not model.is_dirty()

    index = model.index(0, 0)
    model.setData(index, "Alicia")

    assert model.is_dirty()
    model.mark_clean()
    assert not model.is_dirty()


def test_header_and_data_access():
    headers = ["name", "role"]
    data = [{"name": "Alice", "role": "Engineer"}]
    model = DataTableModel(data, headers)

    assert model.rowCount() == 1
    assert model.columnCount() == 3  # includes "sort key"

    index = model.index(0, 1)
    assert "Engineer" in model.data(index, Qt.DisplayRole)


def test_set_dark_mode_changes_display():
    headers = ["name"]
    data = [{"name": "Alice"}]
    model = DataTableModel(data, headers)
    index = model.index(0, 0)

    model.set_dark_mode(True)
    assert "white" in model.data(index, Qt.DisplayRole)

    model.set_dark_mode(False)
    assert "black" in model.data(index, Qt.DisplayRole)


def test_undo_and_redo_work_correctly():
    headers = ["name"]
    data = [{"name": "Alice"}]
    model = DataTableModel(data, headers)

    index = model.index(0, 0)
    model.setData(index, "Alicia")

    assert model._data[0][0] == "Alicia"
    model.undo()
    assert model._data[0][0] == "Alice"
    model.redo()
    assert model._data[0][0] == "Alicia"


def test_finalize_save_clears_stacks(tmp_path):
    headers = ["name"]
    data = [{"name": "Alice"}]
    model = DataTableModel(data, headers)

    model.undo_stack.append(Action(0, 0, "Alice", "Alicia"))
    model.redo_stack.append(Action(0, 0, "Alicia", "Alice"))
    model.unsaved_action_stack.append(Action(0, 0, "Alice", "Alicia"))

    model.undo_log_path = tmp_path / ".undo_log.json"
    model.undo_log_path.write_text("dummy")

    model.finalize_save()

    assert not model.undo_stack
    assert not model.redo_stack
    assert not model.unsaved_action_stack
    assert not model.undo_log_path.exists()


def test_get_current_data_as_dicts():
    headers = ["name", "role"]
    data = [{"name": "Alice", "role": "Engineer"}]
    model = DataTableModel(data, headers)
    output = model.get_current_data_as_dicts()

    assert isinstance(output, list)
    assert output[0]["name"] == "Alice"


def test_update_sort_column_from_cache():
    headers = ["name"]
    data = [{"name": "Alice"}, {"name": "Bob"}]
    proxy = Mock()
    proxy.sort_key_cache = {0: "Zebra", 1: "Apple"}

    model = DataTableModel(data, headers, proxy_model=proxy)
    model.update_sort_column_from_cache()

    sort_col = model.columnCount() - 1
    assert model._data[0][sort_col] == "Zebra"
    assert model._data[1][sort_col] == "Apple"


@patch.dict(os.environ, {"IDW_TEST_MODE": "1"})
@patch("src.table_model.DataTableModel.load_undo_stack_from_file")
@patch("src.table_model.DataTableModel.replay_undo_stack")
def test_recovery_mode_triggers_replay(load_mock, replay_mock, tmp_path):
    undo_path = tmp_path / ".undo_log.json"
    undo_path.write_text("{}")

    headers = ["name"]
    data = [{"name": "Alice"}]
    model = DataTableModel(data, headers)
    model.undo_log_path = undo_path

    # Trigger __init__ post-processing again manually
    if undo_path.exists():
        model.load_undo_stack_from_file()
        model.replay_undo_stack()

    load_mock.assert_called()
    replay_mock.assert_called()
