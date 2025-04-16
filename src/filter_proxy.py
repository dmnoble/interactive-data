from PyQt5.QtCore import QSortFilterProxyModel, Qt


class TableFilterProxyModel(QSortFilterProxyModel):
    def __init__(self):
        super().__init__()
        self.search_text = ""
        self.case_sensitive = False

    def set_search_text(self, text):
        self.search_text = text
        self.invalidateFilter()
        self.layoutChanged.emit()

    def set_case_sensitive(self, enabled):
        self.case_sensitive = enabled
        self.invalidateFilter()
        self.layoutChanged.emit()

    def filterAcceptsRow(self, source_row, source_parent):
        if not self.search_text:
            return True

        model = self.sourceModel()
        column_count = model.columnCount()
        for col in range(column_count):
            index = model.index(source_row, col)
            data = model.data(index, Qt.DisplayRole)
            if data is None:
                continue
            text = str(data)
            if self.case_sensitive:
                if self.search_text in text:
                    return True
            else:
                if self.search_text.lower() in text.lower():
                    return True
        return False
