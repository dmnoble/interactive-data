from src.table_model import DataTableModel
from unittest.mock import Mock


def test_set_data_saves_and_updates():
    headers = ["name", "role"]
    data = [{"name": "Alice", "role": "Engineer"}]  # ✅ Use dicts now

    mock_manager = Mock()
    model = DataTableModel(data, headers, data_manager=mock_manager)

    index = model.index(0, 0)
    new_value = "Alicia"

    result = model.setData(index, new_value)

    assert result is True
    assert model._data[0][0] == "Alicia"
    mock_manager.save_data.assert_called_once()
