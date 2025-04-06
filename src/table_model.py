from PyQt5.QtCore import Qt, QAbstractTableModel
from PyQt5.QtWidgets import QMessageBox


class DataTableModel(QAbstractTableModel):
    def __init__(self, data, headers=None, data_manager=None):
        super().__init__()
        self._raw_data = data or []
        self._data_manager = data_manager

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

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            row = index.row()
            col = index.column()
            self._data[row][col] = value
            self.dataChanged.emit(index, index)

        if self._data_manager:
            try:
                # Convert _data (list of lists) back to list of dicts
                updated_data = [
                    {
                        self._headers[i]: row[i]
                        for i in range(len(self._headers))
                    }
                    for row in self._data
                ]
                self._data_manager.save_data(updated_data)
            except Exception as e:
                QMessageBox.critical(
                    None,
                    "Save Failed",
                    f"An error occurred while saving:\n{str(e)}",
                )
            return True
        return False

    def update_data(self, new_data):
        self.beginResetModel()
        self.__init__(new_data, headers=self._headers)
        self.endResetModel()
