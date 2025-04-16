from PyQt5.QtCore import QSortFilterProxyModel, Qt


class TableFilterProxyModel(QSortFilterProxyModel):
    def __init__(self):
        super().__init__()
        self.search_text = ""

    def set_search_text(self, text):
        self.search_text = text.lower()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        if not self.search_text:
            return True

        model = self.sourceModel()
        column_count = model.columnCount()
        for col in range(column_count):
            index = model.index(source_row, col)
            data = model.data(index, Qt.DisplayRole)
            if self.search_text in str(data).lower():
                return True
        return False
