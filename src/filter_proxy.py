import operator
import logging
from typing import Any

from PyQt5.QtCore import (
    QSortFilterProxyModel,
    Qt,
    QModelIndex,
    pyqtSignal,
)
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
    filterCaseChanged = pyqtSignal(bool)
    filterExprChanged = pyqtSignal(str)
    sortKeyChanged = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self.asteval_engine = Interpreter()
        self.search_text: str = ""
        self.case_sensitive: bool = False
        self.filter_expr: str = ""
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

    def set_filter_expression(self, expr: str) -> None:
        expr = expr.strip()
        if self.filter_expr == expr:
            return
        self.filter_expr = expr
        self.invalidateFilter()
        self.layoutChanged.emit()
        self.filterExprChanged.emit(self.filter_expr)

    def set_case_sensitive(self, enabled: bool) -> None:
        if self.case_sensitive == enabled:
            return
        self.case_sensitive = enabled
        self.invalidateFilter()
        self.layoutChanged.emit()
        self.filterCaseChanged.emit(enabled)

    def set_custom_sort_key(self, expr: str) -> None:
        expr = expr.strip()
        if self.custom_sort_key == expr:
            return
        self.custom_sort_key = expr
        self.sort_key_cache.clear()
        self.sortKeyChanged.emit(self.custom_sort_key)

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
        self.rebuild_sort_key_cache()

    def filterAcceptsRow(
        self, source_row: int, source_parent: QModelIndex
    ) -> bool:
        model = self.sourceModel()
        if model is None:
            return False

        # Set search text ONLY if expression is a simple word
        if self.filter_expr and (
            self.filter_expr.isdigit() or self.filter_expr.isalpha()
        ):
            for col in range(model.columnCount()):
                index = model.index(source_row, col)
                data = model.data(index, Qt.DisplayRole)
                if data is None:
                    continue
                text = str(data)
                if self.case_sensitive and self.filter_expr in text:
                    return True
                elif (
                    not self.case_sensitive
                    and self.filter_expr.lower() in text.lower()
                ):
                    return True
            return False

        # custom expression
        else:
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
                    expr = self.filter_expr.lower()
                else:
                    expr = self.filter_expr

                self.asteval_engine.symtable.clear()
                self.asteval_engine.symtable.update(row_dict)
                result = self.asteval_engine(expr)

                if not result:
                    return False

            except Exception:
                return False
        return True

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
                    val = ""
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
