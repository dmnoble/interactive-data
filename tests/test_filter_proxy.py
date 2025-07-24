from PyQt5.QtCore import Qt, QModelIndex, QAbstractTableModel
from src.models.filter_proxy import TableFilterProxyModel


class DummyModel(QAbstractTableModel):
    def __init__(self):
        super().__init__()
        self.rowCount_called = False
        self.data_called = []

        self._headers = ["id", "name"]
        self._data = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
            {"id": 3, "name": "Charlie"},
        ]

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    def index(self, row, column, parent=QModelIndex()):
        return self.createIndex(row, column)

    def data(self, index, role=Qt.DisplayRole):
        self.data_called.append((index, role))
        if not index.isValid():
            return None
        key = self._headers[index.column()]
        value = self._data[index.row()][key]
        if role in (Qt.DisplayRole, TableFilterProxyModel.RAW_VALUE_ROLE):
            return value
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._headers[section]
        return None


class DummyIndex(QModelIndex):
    def __init__(self, row, col):
        super().__init__()
        self._row = row
        self._col = col

    def row(self):
        return self._row

    def column(self):
        return self._col


def test_set_filter_expression_emits():
    proxy = TableFilterProxyModel()
    changed = []

    proxy.filterExprChanged.connect(lambda expr: changed.append(expr))
    proxy.set_filter_expression("age > 30")

    assert proxy.filter_expr == "age > 30"
    assert changed == ["age > 30"]


def test_set_case_sensitive_emits():
    proxy = TableFilterProxyModel()
    changed = []

    proxy.filterCaseChanged.connect(lambda enabled: changed.append(enabled))
    proxy.set_case_sensitive(True)

    assert proxy.case_sensitive is True
    assert changed == [True]


def test_set_custom_sort_key_builds_cache():
    proxy = TableFilterProxyModel()
    model = DummyModel()

    # Attach model
    proxy.setSourceModel(model)
    changed = []
    proxy.sortKeyChanged.connect(lambda expr: changed.append(expr))

    proxy.set_custom_sort_key("len(name)")

    # Check cache created
    assert 0 in proxy.sort_key_cache
    assert proxy.sort_key_cache[0] == 5  # len("Alice")
    assert changed.count("len(name)") >= 1
    assert len(proxy.sort_key_cache) == model.rowCount()
    assert len(model.data_called) > 0


def test_case_sensitive_filtering():
    proxy = TableFilterProxyModel()
    model = DummyModel()
    proxy.setSourceModel(model)

    # Case-sensitive: should not match "alice" with "Alice"
    proxy.set_filter_expression("alice")
    proxy.set_case_sensitive(True)

    accepted = [
        proxy.filterAcceptsRow(row, QModelIndex())
        for row in range(model.rowCount())
    ]
    assert accepted == [False, False, False]  # no match due to case

    # Case-insensitive: should match "alice" with "Alice"
    proxy.set_case_sensitive(False)
    accepted = [
        proxy.filterAcceptsRow(row, QModelIndex())
        for row in range(model.rowCount())
    ]
    assert accepted == [True, False, False]  # match on first row


def test_filter_expression_partial_match():
    proxy = TableFilterProxyModel()
    model = DummyModel()
    proxy.setSourceModel(model)
    proxy.set_filter_expression("li")

    matched_rows = [
        i
        for i in range(model.rowCount())
        if proxy.filterAcceptsRow(i, QModelIndex())
    ]
    assert matched_rows == [0, 2]  # Alice and Charlie contain "li"


def test_empty_filter_matches_all():
    proxy = TableFilterProxyModel()
    model = DummyModel()
    proxy.setSourceModel(model)
    proxy.set_filter_expression("")

    all_rows = [
        proxy.filterAcceptsRow(i, QModelIndex())
        for i in range(model.rowCount())
    ]
    assert all(all_rows)


def test_set_case_sensitive_flag_behavior():
    proxy = TableFilterProxyModel()
    assert not proxy.case_sensitive
    proxy.set_case_sensitive(True)
    assert proxy.case_sensitive
    proxy.set_case_sensitive(False)
    assert not proxy.case_sensitive
