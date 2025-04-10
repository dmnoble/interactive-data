from PyQt5.QtCore import Qt, QAbstractTableModel


class DataTableModel(QAbstractTableModel):
    def __init__(self, data, headers=None, data_manager=None):
        super().__init__()
        self._raw_data = data or []
        self._data_manager = data_manager
        self._dirty = False
        self._backup_dirty = False

        if headers:
            self._headers = headers
        else:
            self._headers = (
                list(self._raw_data[0].keys()) if self._raw_data else []
            )

        self._data = [
            [item.get(header, "") for header in self._headers]
            for item in self._raw_data
        ]

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self._headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole or role == Qt.EditRole:
            row = index.row()
            col = index.column()
            return self._data[row][col]
        return None

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._headers[section]
            else:
                return str(section)
        return None

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def is_dirty(self):
        return self._dirty

    def is_backup_dirty(self):
        return self._backup_dirty

    def mark_clean(self):
        self._dirty = False

    def mark_backup_clean(self):
        self._backup_dirty = False

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            row = index.row()
            col = index.column()
            current_value = self._data[row][col]

            if current_value == value:
                return False  # No change → no dirty flag

            self._data[row][col] = value
            self._dirty = True
            self._backup_dirty = True
            self.dataChanged.emit(index, index)
            # Let auto-save handle the actual save
            return True
        return False

    def update_data(self, new_data):
        self.beginResetModel()
        self.__init__(new_data, headers=self._headers)
        self.endResetModel()

    def get_current_data_as_dicts(self):
        return [
            {self._headers[i]: row[i] for i in range(len(self._headers))}
            for row in self._data
        ]
