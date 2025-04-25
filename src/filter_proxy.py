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

    RAW_VALUE_ROLE = Qt.UserRole + 1

    def __init__(self):
        super().__init__()
        self.asteval_engine = Interpreter()
        self.search_text = ""
        self.case_sensitive = False
        self.custom_expr = ""
        self.structured_filter = {"field": "", "operator": "", "value": ""}
        self.custom_sort_key = ""

        self.base_symbols = {
            "len": len,
            "abs": abs,
            "min": min,
            "max": max,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "round": round,
        }

    def set_search_text(self, text):
        self.search_text = text
        self.invalidateFilter()
        self.layoutChanged.emit()

    def set_case_sensitive(self, enabled):
        self.case_sensitive = enabled
        self.invalidateFilter()
        self.layoutChanged.emit()

    def set_custom_sort_key(self, expr):
        self.custom_sort_key = expr.strip()
        self.invalidate()

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

                    # Handle operator logic by type
                    if isinstance(data, str):
                        if op == "contains":
                            if target_casted not in data:
                                return False
                        elif op == "startswith":
                            if not data.startswith(target_casted):
                                return False
                        elif op == "endswith":
                            if not data.endswith(target_casted):
                                return False
                        elif op == "matches":
                            if (
                                target_casted not in data
                            ):  # simple match = substring for now
                                return False
                        elif op == "not":
                            if target_casted in data:
                                return False
                        else:
                            return False  # unsupported string op

                    elif op in OPS:
                        if not OPS[op](data, target_casted):
                            return False
                    else:
                        return False  # unknown op

                except Exception:
                    return False  # Fail-safe: exclude row if filtering fails

        # Simple text search handling
        if self.search_text and not self.custom_expr:
            column_count = model.columnCount()
            match_found = False
            for col in range(column_count):
                index = model.index(source_row, col)
                data = model.data(index, Qt.DisplayRole)
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

        # Step 2: custom expression
        if self.custom_expr:
            try:
                row_dict = {}
                headers = model._headers
                for col_index, header in enumerate(headers):
                    index = model.index(source_row, col_index)
                    value = model.data(index, self.RAW_VALUE_ROLE)
                    row_dict[header] = value

                expr = self.custom_expr
                if not self.case_sensitive:
                    # Lowercase everything for comparison if case-insensitive
                    row_dict = {
                        k: v.lower() if isinstance(v, str) else v
                        for k, v in row_dict.items()
                    }
                    expr = expr.lower()

                self.asteval_engine.symtable.clear()
                self.asteval_engine.symtable.update(row_dict)
                result = self.asteval_engine(expr)

                if not result:
                    return False

            except Exception:
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

    def lessThan(self, left, right):
        model = self.sourceModel()

        row_left = {}
        row_right = {}
        headers = model._headers
        for col_index, header in enumerate(headers):
            index_left = model.index(left.row(), col_index)
            index_right = model.index(right.row(), col_index)
            row_left[header] = model.data(index_left, self.RAW_VALUE_ROLE)
            row_right[header] = model.data(index_right, self.RAW_VALUE_ROLE)

        if self.custom_sort_key:
            try:
                self.asteval_engine.symtable = self.base_symbols.copy()
                self.asteval_engine.symtable.update(row_left)
                val_left = self.asteval_engine(self.custom_sort_key)

                self.asteval_engine.symtable = self.base_symbols.copy()
                self.asteval_engine.symtable.update(row_right)
                val_right = self.asteval_engine(self.custom_sort_key)

                return val_left < val_right
            except Exception as e:
                print(f"Sort expression error: {e}")
                return False
        return super().lessThan(left, right)
