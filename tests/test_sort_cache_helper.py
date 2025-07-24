import pytest
from unittest.mock import MagicMock
from src.services.sort_cache_helper import SortCacheHelper
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt


class DummyTableModel(QAbstractTableModel):
    def __init__(self):
        super().__init__()
        self._data = [["" for _ in range(2)] for _ in range(3)]
        self._raw_data = [{"sort_key": ""} for _ in range(3)]
        self._headers = ["name", "sort_key"]

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._data[0]) if self._data else 0

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and index.isValid():
            return self._data[index.row()][index.column()]
        return None

    def index(self, row, column, parent=QModelIndex()):
        return self.createIndex(row, column)


@pytest.fixture
def sort_cache():
    return SortCacheHelper()


def test_apply_sort_cache_updates_model(sort_cache):
    model = DummyTableModel()
    sort_cache_dict = {0: "zebra", 1: "apple", 2: "monkey"}

    SortCacheHelper.apply_sort_cache_to_model(model, sort_cache_dict)

    assert model._raw_data[0]["sort_key"] == "zebra"
    assert model._raw_data[1]["sort_key"] == "apple"
    assert model._raw_data[2]["sort_key"] == "monkey"

    assert model._data[0][1] == "zebra"
    assert model._data[1][1] == "apple"
    assert model._data[2][1] == "monkey"


def test_clear_sort_column_removes_column_values(sort_cache):
    model = DummyTableModel()
    model._data[0][1] = "sort1"
    model._data[1][1] = "sort2"
    model._data[2][1] = "sort3"

    SortCacheHelper.clear_sort_column(model)

    assert model._data[0][1] == ""
    assert model._data[1][1] == ""
    assert model._data[2][1] == ""


def test_emit_called(qtbot):
    model = DummyTableModel()
    spy = MagicMock()
    model.dataChanged.connect(spy)

    model._data[0][1] = "zebra"
    idx = model.index(0, 1)
    model.dataChanged.emit(idx, idx)

    spy.assert_called_once()


def test_apply_sort_cache_to_model_normal_case():
    model = DummyTableModel()
    model._headers.append("sort_key")  # simulate column to store sort value
    model._data = [["a", ""], ["b", ""]]
    model._raw_data = [{"name": "Alice"}, {"name": "Bob"}]

    sort_cache = {0: "zebra", 1: "apple"}
    SortCacheHelper.apply_sort_cache_to_model(model, sort_cache, sort_column=1)

    assert model._data[0][1] == "zebra"
    assert model._data[1][1] == "apple"
    assert model._raw_data[0]["sort_key"] == "zebra"
    assert model._raw_data[1]["sort_key"] == "apple"


def test_apply_sort_cache_to_model_default_column():
    model = DummyTableModel()
    model._headers.extend(["name", "sort_key"])
    model._data = [["foo", ""], ["bar", ""]]
    model._raw_data = [{"name": "one"}, {"name": "two"}]

    cache = {0: "zzz", 1: "aaa"}
    SortCacheHelper.apply_sort_cache_to_model(model, cache)

    assert model._data[0][-1] == "zzz"
    assert model._data[1][-1] == "aaa"


def test_apply_sort_cache_to_model_skips_invalid_indices():
    model = DummyTableModel()
    model._headers.append("sort_key")
    model._data = [["only one row", ""]]
    model._raw_data = [{"name": "uno"}]

    cache = {0: "valid", 1: "should be skipped"}
    SortCacheHelper.apply_sort_cache_to_model(model, cache, sort_column=1)

    assert model._data[0][1] == "valid"
    assert model._raw_data[0]["sort_key"] == "valid"
