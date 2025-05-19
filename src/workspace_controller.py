# workspace_controller.py

from config import load_config, save_config
from data_manager import DataManager
from table_model import DataTableModel
from view_config import get_default_view_name
from rich_text_delegate import RichTextDelegate
from PyQt5.QtCore import QTimer, Qt, QDateTime
from PyQt5.QtWidgets import QHeaderView, QTableView
from view_config import save_view_config, get_view_config
from filter_proxy import TableFilterProxyModel


class WorkspaceController:
    def __init__(self):
        self.profile_name = ""
        self.data_manager = DataManager()
        self.table_view = QTableView()
        self.config = None
        self.model = None
        self.proxy_model = TableFilterProxyModel()

        # Search
        self.table_view.setTextElideMode(Qt.ElideNone)  # allow wrapping

    def undo(self):
        self.model.undo()

    def redo(self):
        self.model.redo()

    def load_profile(self, new_profile_name: str):
        if new_profile_name == self.profile_name:
            return  # No-op if same

        self.check_dirty_and_save()
        self.profile_name = new_profile_name
        self.config = load_config(new_profile_name)

        return self.config

    def load_data(self, update_undo_redo_history):
        # Load real data from DataManager
        raw_data = self.data_manager.load_data(self.profile_name)

        # Dynamically get headers from first item (or fallback)
        headers = list(raw_data[0].keys()) if raw_data else []

        is_first_model = False
        if not self.model:
            is_first_model = True

        # Create the model
        self.model = DataTableModel(
            raw_data,
            headers,
            data_manager=self.data_manager,
            proxy_model=self.proxy_model,
            dark_mode=self.config.get("dark_mode", False),
        )
        self.proxy_model.setSourceModel(self.model)

        if is_first_model:
            # Connect to model update:
            self.model.stack_changed.connect(
                lambda: update_undo_redo_history(
                    self.model.undo_stack, self.model.redo_stack
                )
            )
            print("Initalized model")
            self.table_view.setModel(self.proxy_model)
            self.table_view.setSortingEnabled(True)  # Only works through proxy

        return headers

    def check_dirty_and_save(self):
        if self.model and self.model.is_dirty():
            try:
                data = self.model.get_current_data_as_dicts()
                self.data_manager.save_data(data, self.profile_name)
                self.last_save_time = QDateTime.currentDateTime()
                self.model.finalize_save()
                print("Auto-save complete.")
            except Exception as e:
                print("Auto-save failed:", e)

    def auto_backup_if_needed(self):
        """
        Auto-Backup every hour and on close
        """
        if self.model and self.model.is_backup_dirty():
            try:
                data = self.model.get_current_data_as_dicts()
                self.data_manager.save_backup(data, self.profile_name)
                self.model.mark_backup_clean()
            except Exception as e:
                print("Auto-backup failed:", e)

    def get_default_view(self):
        return get_default_view_name(self.profile_name)

    def load_view_config(self, view_name):
        cleaned_name = view_name.replace(" (default)", "")

        config = get_view_config(cleaned_name, self.profile_name)
        if not config:
            return

        filter_text = config.get("search_text", "")
        self.proxy_model.set_custom_filter_expression(filter_text)
        self.proxy_model.set_search_text(
            filter_text if filter_text.isalnum() else ""
        )
        filter_cfg = config.get("filter", {})
        self.proxy_model.set_structured_filter(
            filter_cfg.get("field", ""),
            filter_cfg.get("operator", "=="),
            filter_cfg.get("value", ""),
        )

        # self.table_view.sortByColumn(
        #     config.get("sort_column", 0),
        #     (
        #         Qt.AscendingOrder
        #         if config.get("ascending", True)
        #         else Qt.DescendingOrder
        #     ),
        # )

        return cleaned_name, config

    def save_theme_to_config(self, is_dark):
        self.config["dark_mode"] = is_dark
        save_config(self.config, self.profile_name)
        if self.model:
            self.model.set_dark_mode(self.config["dark_mode"])

    def save_view_config(
        self,
        name,
        custom_expr,
        case_sensitive,
        field,
        operator,
        value,
        sort_key,
    ):
        ascending = (
            self.table_view.horizontalHeader().sortIndicatorOrder()
            == Qt.AscendingOrder
        )
        config = {
            "name": name,
            "filter_text": custom_expr,
            "case_sensitive": case_sensitive,
            "sort_column": (
                self.table_view.horizontalHeader().sortIndicatorSection()
            ),
            "ascending": ascending,
            "filter": {
                "field": field,
                "operator": operator,
                "value": value,
            },
            "custom_filter": custom_expr,
            "custom_sort_key": sort_key,
        }
        save_view_config(name, config, self.profile_name)

    def apply_to_view(self):
        """Hook up delegate, model, etc. to a QTableView."""
        if not self.model:
            return

        # Render HTML in cells — including the fancy
        # substring <span style=...> highlights from search.
        self.table_view.setItemDelegate(RichTextDelegate())
        self.table_view.setSortingEnabled(True)
        self.table_view.setWordWrap(False)
        self.table_view.setTextElideMode(Qt.ElideRight)
        # Start compact: auto-size to content initially
        self.table_view.horizontalHeader().setStretchLastSection(False)
        self.table_view.horizontalHeader().setSectionResizeMode(
            QHeaderView.Interactive
        )
        # Give Qt a moment to measure based on the new delegate rendering
        QTimer.singleShot(0, self.table_view.resizeColumnsToContents)

        # self.table_view.setWordWrap(False)
        # self.table_view.setTextElideMode(Qt.ElideRight)

    def apply_custom_sort(self, sort_key, ascending):
        if not sort_key:
            return

        # This fixes (somehow) the issue of the sorting sometimes
        # reverting to column 0 (id) even when there is a sort_key
        self.table_view.sortByColumn(0, Qt.AscendingOrder)

        self.proxy_model.set_custom_sort_key(sort_key)
        self.proxy_model.rebuild_sort_key_cache()

        # 🛠 Inject sort result values directly into DataTableModel
        if self.model and self.proxy_model.sort_key_cache:
            for (
                proxy_row,
                sort_value,
            ) in self.proxy_model.sort_key_cache.items():
                if 0 <= proxy_row < len(self.model._data):
                    self.model._data[proxy_row][-1] = str(sort_value)

        # ✅ Visually apply saved sort direction (fallback)
        sort_order = Qt.AscendingOrder if ascending else Qt.DescendingOrder
        headers = self.model._headers

        sort_column = headers.index("sort key") if "sort key" in headers else 0
        self.table_view.sortByColumn(sort_column, sort_order)
        self.table_view.horizontalHeader().setSortIndicator(
            sort_column, sort_order
        )
        self.table_view.horizontalHeader().setSortIndicatorShown(True)

    def clear_custom_sort(self):
        self.proxy_model.set_custom_sort_key("")
        self.proxy_model.sort_key_cache.clear()

        if self.model:
            sort_column = self.model.columnCount() - 1
            for row_index in range(len(self.model._data)):
                self.model._data[row_index][sort_column] = ""
                index = self.model.index(row_index, sort_column)
                self.model.dataChanged.emit(index, index)

        self.table_view.sortByColumn(0, Qt.AscendingOrder)

    def update_filter_operators(self, field):
        sample_value = None
        headers = self.model._headers
        if field in headers:
            col_index = headers.index(field)
            for row in range(self.model.rowCount()):
                index = self.model.index(row, col_index)
                value = self.model.data(index, self.proxy_model.RAW_VALUE_ROLE)
                if value is not None:
                    sample_value = value
                    break
        return sample_value

    def update_custom_filter_expr(self, expr):
        self.proxy_model.set_custom_filter_expression(expr)

        # Set search text ONLY if expression is a simple word
        if expr and (expr.isdigit() or expr.isalpha()):
            self.proxy_model.set_search_text(expr)
            self.proxy_model.set_custom_filter_expression("")
        else:
            self.proxy_model.set_search_text("")
            self.proxy_model.set_custom_filter_expression(expr)

    def update_structured_filter(self, field, op, value):
        self.proxy_model.set_structured_filter(field, op, value)

    def clear_custom_filter(self):
        self.proxy_model.set_custom_filter_expression("")
        self.proxy_model.set_search_text("")  # reset search text too

    def apply_structured_filter(self, combined_expr):
        self.proxy_model.set_custom_filter_expression(combined_expr)

        # Reset sort to original order if no sort key is active
        if not self.proxy_model.custom_sort_key:
            self.table_view.horizontalHeader().setSortIndicator(
                -1, Qt.AscendingOrder
            )

    def set_case_sensitive(self, state):
        self.proxy_model.set_case_sensitive(state)
