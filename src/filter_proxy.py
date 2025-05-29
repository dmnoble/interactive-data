import operator
import logging
from typing import Optional, Any

from PyQt5.QtCore import QSortFilterProxyModel, Qt, QModelIndex
from asteval import Interpreter

logger = logging.getLogger(__name__)


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

    def __init__(self) -> None:
        super().__init__()
        self.asteval_engine = Interpreter()
        self.search_text: str = ""
        self.case_sensitive: bool = False
        self.custom_expr: str = ""
        self.structured_filter: Optional[dict] = None
        self.custom_sort_key: str = ""
        self.sort_key_cache: dict[int, Any] = (
            {}
        )  # stores sort key results per row

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

    def set_search_text(self, text: str) -> None:
        self.search_text = text
        self.invalidateFilter()
        self.layoutChanged.emit()

    def set_case_sensitive(self, enabled: bool) -> None:
        self.case_sensitive = enabled
        self.invalidateFilter()
        self.layoutChanged.emit()

    def set_custom_sort_key(self, expr: str) -> None:
        self.custom_sort_key = expr.strip()
        self.sort_key_cache.clear()

        model = self.sourceModel()
        if model is None:
            return

        headers = getattr(model, "_headers", [])
        for row_index in range(model.rowCount()):
            row_data = {
                header: model.data(
                    model.index(row_index, col), self.RAW_VALUE_ROLE
                )
                for col, header in enumerate(headers)
            }
            try:
                scope = {**self.base_symbols, **row_data}
                self.asteval_engine.symtable.clear()
                self.asteval_engine.symtable.update(scope)
                result = self.asteval_engine(self.custom_sort_key)
            except Exception:
                result = "ERROR"
            # Optionally, store the result in a cache or handle as needed
            self.sort_key_cache[row_index] = result

        model.layoutChanged.emit()
        self.invalidate()

    def filterAcceptsRow(
        self, source_row: int, source_parent: QModelIndex
    ) -> bool:
        model = self.sourceModel()

        # Simple text search handling
        if self.search_text and not self.custom_expr:
            for col in range(model.columnCount()):
                index = model.index(source_row, col)
                data = model.data(index, Qt.DisplayRole)
                if data is None:
                    continue
                text = str(data)
                if self.case_sensitive and self.search_text in text:
                    return True
                elif (
                    not self.case_sensitive
                    and self.search_text.lower() in text.lower()
                ):
                    return True
            return False

        # custom expression
        if self.custom_expr:
            try:
                headers = getattr(model, "_headers", [])
                row_dict = {
                    header: model.data(
                        model.index(source_row, i), self.RAW_VALUE_ROLE
                    )
                    for i, header in enumerate(headers)
                }

                if not self.case_sensitive:
                    row_dict = {
                        k: v.lower() if isinstance(v, str) else v
                        for k, v in row_dict.items()
                    }
                    expr = self.custom_expr.lower()
                else:
                    expr = self.custom_expr

                self.asteval_engine.symtable.clear()
                self.asteval_engine.symtable.update(row_dict)
                result = self.asteval_engine(expr)

                if not result:
                    return False

            except Exception:
                return False
        return True

    def set_structured_filter(
        self, field: str, operator_: str, value: str
    ) -> None:
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

    def set_custom_filter_expression(self, expr: str) -> None:
        self.custom_expr = expr.strip()
        self.invalidateFilter()
        self.layoutChanged.emit()

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        model = self.sourceModel()

        if self.custom_sort_key:
            val_left = self.sort_key_cache.get(left.row(), "")
            val_right = self.sort_key_cache.get(right.row(), "")
            try:
                return val_left < val_right
            except SyntaxError as e:
                logger.warning(f"Custom filter syntax error: {e}")
                logger.warning(f"Expression was: {self.custom_sort_key}")
                return False
            except Exception as e:
                logger.warning(f"Custom filter evaluation error: {e}")
                return False

        left_val = model.data(left, self.RAW_VALUE_ROLE)
        right_val = model.data(right, self.RAW_VALUE_ROLE)
        try:
            return left_val < right_val
        except Exception:
            return False

    def rebuild_sort_key_cache(self) -> None:
        self.sort_key_cache.clear()
        model = self.sourceModel()
        if not model:
            return

        headers = getattr(model, "_headers", [])
        for row in range(model.rowCount()):
            row_dict = {
                header: model.data(model.index(row, i), self.RAW_VALUE_ROLE)
                for i, header in enumerate(headers)
            }

            if self.custom_sort_key:
                try:
                    self.asteval_engine.symtable.clear()
                    # 🛠 First inject built-ins
                    self.asteval_engine.symtable.update(self.base_symbols)
                    # 🛠 Then inject row fields
                    self.asteval_engine.symtable.update(row_dict)
                    try:
                        val = self.asteval_engine(self.custom_sort_key)
                    except SyntaxError as e:
                        logger.warning(f"Custom filter syntax error: {e}")
                        logger.warning(
                            f"Expression was: {self.custom_sort_key}"
                        )
                    except Exception as e:
                        logger.warning(f"Custom filter evaluation error: {e}")
                    self.sort_key_cache[row] = val
                except Exception as e:
                    logger.warning(f"Sort key error at row {row}: {e}")
                    self.sort_key_cache[row] = ""
