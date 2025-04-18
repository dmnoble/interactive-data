from PyQt5.QtCore import QSortFilterProxyModel, Qt
from asteval import Interpreter
import operator

OPS = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    "<": operator.lt,
    ">=": operator.ge,
    "<=": operator.le,
}


class TableFilterProxyModel(QSortFilterProxyModel):

    asteval_engine = Interpreter()
    structured_filter = {"field": "", "operator": "", "value": ""}
    RAW_VALUE_ROLE = Qt.UserRole + 1

    def __init__(self):
        super().__init__()
        self.search_text = ""
        self.case_sensitive = False
        self.custom_expr = ""

    def set_search_text(self, text):
        self.search_text = text
        self.invalidateFilter()
        self.layoutChanged.emit()

    def set_case_sensitive(self, enabled):
        self.case_sensitive = enabled
        self.invalidateFilter()
        self.layoutChanged.emit()

    def filterAcceptsRow(self, source_row, source_parent):
        model = self.sourceModel()

        # Step 1: check structured filter first (if set)
        if self.structured_filter:
            field = self.structured_filter.get("field")
            op = self.structured_filter.get("operator")
            target = self.structured_filter.get("value")

            if field and op and target:
                try:
                    column_index = model._headers.index(field)
                    index = model.index(source_row, column_index)
                    data = model.data(index, self.RAW_VALUE_ROLE)

                    if data is None:
                        return True  # Don't exclude the row

                    # Try to auto-convert target to match data type
                    if isinstance(data, (int, float)):
                        target_casted = type(data)(target)
                    elif isinstance(data, bool):
                        target_casted = target.lower() in ["true", "1", "yes"]
                    else:
                        target_casted = str(target)

                    if not OPS[op](data, target_casted):
                        return False

                except Exception:
                    return False  # Fail-safe: exclude row if filtering fails

        # Step 2: search filter (applies across all columns)
        if self.search_text:
            column_count = model.columnCount()
            match_found = False
            for col in range(column_count):
                index = model.index(source_row, col)
                data = model.data(index, self.RAW_VALUE_ROLE)
                if data is None:
                    continue
                text = str(data)
                if self.case_sensitive:
                    if self.search_text in text:
                        match_found = True
                        break
                else:
                    if self.search_text.lower() in text.lower():
                        match_found = True
                        break
            if not match_found:
                return False

        # Step 3: custom expression
        if self.custom_expr:
            try:
                row_dict = {}
                headers = model._headers
                for col_index, header in enumerate(headers):
                    index = model.index(source_row, col_index)
                    value = model.data(index, self.RAW_VALUE_ROLE)
                    row_dict[header] = value
                    self.asteval_engine.symtable.clear()
                    self.asteval_engine.symtable.update(row_dict)
                    result = self.asteval_engine(self.custom_expr)
                if not result:
                    return False
            except Exception:
                # except Exception as e:
                # print(f"Custom filter error: {e}")
                return False

        return True

    def set_structured_filter(self, field, operator_, value):
        if field and operator_ and value:
            self.structured_filter = {
                "field": field.strip(),
                "operator": operator_.strip(),
                "value": value.strip(),
            }
        else:
            self.structured_filter = None
        self.invalidateFilter()
        self.layoutChanged.emit()

    def set_custom_filter_expression(self, expr):
        self.custom_expr = expr.strip()
        self.invalidateFilter()
        self.layoutChanged.emit()
