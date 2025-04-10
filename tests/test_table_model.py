from src.table_model import DataTableModel
from unittest.mock import Mock


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
    mock_manager.save_data.assert_not_called()  # save_data is not expected


def test_dirty_flag_on_data_change():
    headers = ["name", "role"]
    data = [{"name": "Alice", "role": "Engineer"}]
    model = DataTableModel(data, headers)

    # Initially not dirty
    assert not model.is_dirty()

    # Modify the data
    index = model.index(0, 0)  # "name" column
    model.setData(index, "Alicia")

    assert model.is_dirty(), "Dirty flag should be set after change"

    # Reset dirty flag manually
    model.mark_clean()
    assert not model.is_dirty(), "Dirty flag should reset with mark_clean"
