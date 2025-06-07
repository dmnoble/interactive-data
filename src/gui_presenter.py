from filter_proxy import TableFilterProxyModel
from workspace_controller import WorkspaceController
from gui import BuildGui
from utils import get_save_time_label_text
from proxy_model_service import ProxyModelService

import logging
import sys
from rich_text_delegate import RichTextDelegate
from PyQt5.QtWidgets import (
    QTableView,
    QShortcut,
    QHeaderView,
    QInputDialog,
    QMessageBox,
)
from PyQt5.QtGui import QKeySequence, QPalette
from PyQt5.QtCore import Qt, QTimer, QDateTime


logger = logging.getLogger(__name__)


class GuiPresenter:
    def __init__(self, controller: WorkspaceController, gui: BuildGui) -> None:
        self.controller = controller
        self.proxy_model = TableFilterProxyModel()
        self.model = None
        self.gui = gui

        self.setup_table_view()
        self.set_auto_saves()

        # Populate view names at startup
        self.view_selector_populate_set_to_default()
        # Check if profiles exist, if not prompt user for a new one
        self.gui.update_profile_list(self.controller.get_profiles())
        if not self.gui.profile_selector.count():
            QTimer.singleShot(
                0, self.create_new_profile
            )  # defer profile creation
        # Generate self.model but requires elements initiated
        # along with populated theme and profile selectors
        self.on_profile_changed()
        self.connect_signals()

    def set_auto_saves(self):
        # Autosave timer
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(
            self.controller.check_dirty_and_save
        )
        self.auto_save_timer.start(60_000)  # Every minute

        # GUI label for time since last save
        self.last_save_time = QDateTime.currentDateTime()
        self.save_timer = QTimer()
        self.save_timer.timeout.connect(self.update_save_label)
        self.save_timer.start(30 * 1000)  # every half minute

        # Timer for the hourly backup
        self.backup_timer = QTimer()
        self.backup_timer.timeout.connect(
            self.controller.auto_backup_if_needed
        )
        self.backup_timer.start(60 * 60 * 1000)  # every hour in ms)

    def setup_table_view(self):
        self.table_view: QTableView = self.gui.table_view
        self.table_view.setModel(self.proxy_model)
        self.table_view.setItemDelegate(RichTextDelegate())
        self.table_view.setSortingEnabled(True)
        self.table_view.setWordWrap(False)
        self.table_view.setTextElideMode(Qt.ElideRight)

    def connect_signals(self) -> None:
        """
        Connects signals to their respective slots.
        """
        self.gui.profile_selector.currentIndexChanged.connect(
            self.on_profile_changed
        )
        self.gui.add_profile_button.clicked.connect(self.create_new_profile)

        self.gui.theme_selector.currentIndexChanged.connect(
            lambda: self.gui.setPalette(self.apply_theme())
        )

        # Connect apply custom sort button
        self.gui.apply_sort_button.clicked.connect(self.apply_custom_sort)

        # Connect clear filter button
        self.gui.clear_filter_button.clicked.connect(self.on_clear_filter)

        # Data handling
        self.gui.case_checkbox.stateChanged.connect(
            lambda state: self.proxy_model.set_case_sensitive(
                state == Qt.Checked
            )
        )

        # Save view button
        self.gui.save_view_button.clicked.connect(self.on_save_current_view)

        # View loader dropdown
        self.gui.view_selector.activated[str].connect(self.load_selected_view)

        # Default view button
        self.gui.set_default_button.clicked.connect(self.on_set_default_view)

        # Filter
        self.gui.field_selector.currentTextChanged.connect(
            self.gui.update_filter_operators
        )
        self.gui.structured_ok_button.clicked.connect(
            self.apply_structured_filter
        )
        self.gui.custom_filter_input.textChanged.connect(
            self.update_custom_filter_expr
        )

        # Sort
        self.gui.clear_sort_button.clicked.connect(self.on_clear_custom_sort)

        # Undo redo
        self.gui.undo_button.clicked.connect(self.controller.undo)
        self.gui.redo_button.clicked.connect(self.controller.redo)

        # Add shortcuts:
        undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self.gui)
        redo_shortcut = QShortcut(QKeySequence("Ctrl+Y"), self.gui)
        undo_shortcut.activated.connect(self.controller.undo)
        redo_shortcut.activated.connect(self.controller.redo)

    def update_save_label(self) -> None:
        text = get_save_time_label_text(self.last_save_time)
        self.gui.update_save_label(text)

    def on_profile_changed(self) -> None:
        current_profile = self.gui.profile_selector.currentText()
        config = self.controller.load_profile(current_profile)
        if not config:
            return
        model, headers = self.controller.load_data(self.proxy_model)
        self.proxy_model.setSourceModel(model)

        # Connect to model update
        model.stack_changed.connect(
            lambda: self.gui.update_undo_redo_history(
                model.undo_stack, model.redo_stack
            )
        )

        """Hook up delegate, model, etc. to a QTableView."""
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

        self.update_save_label()

        self.gui.theme_selector.setCurrentText(
            "Dark" if config.is_dark_mode() else "Light"
        )
        self.gui.setPalette(self.apply_theme())

        self.gui.field_selector.clear()
        self.gui.field_selector.addItems(headers)
        self.update_filter_operators()  # Run after headers added

        # make sure the dropdown is populated
        self.view_selector_populate_set_to_default()

        default_view = self.controller.get_default_view()
        if default_view:
            self.load_selected_view(default_view)

            # 🛠 Force Apply Sort logic on startup
            expr = self.gui.custom_sort_input.currentText().strip()
            if expr:
                self.apply_custom_sort()
            self.gui.set_view_selector(f"{default_view} (default)")
        else:
            self.on_clear_filter()
            self.on_clear_custom_sort()

        # Clear history dropdowns
        self.gui.undo_history_combo.clear()
        self.gui.redo_history_combo.clear()

        logger.info(f"Switched to profile: {current_profile}")

    def create_new_profile(self) -> None:
        """
        Prompts the user to enter a new profile name
        """
        dialog = QInputDialog(self.gui)
        dialog.setPalette(self.apply_theme())
        new_profile, ok = dialog.getText(
            self.gui, "New Profile", "Enter profile name:"
        )
        if ok and new_profile and not new_profile.strip() == "":
            created = self.controller.create_profile(new_profile)
            if created:
                self.gui.update_profile_list(self.controller.get_profiles())
                index = self.gui.profile_selector.findText(new_profile)
                if index != -1:
                    self.gui.profile_selector.setCurrentIndex(index)
                logger.info(f"New profile created for {new_profile}")
            else:
                QMessageBox.warning(
                    self.gui,
                    "Profile Exists",
                    f"The profile '{new_profile}' already exists.",
                )

        if not self.gui.profile_selector.count():
            sys.exit(
                "No profiles available. Please create a new "
                + "profile to continue."
            )

    def closeEvent(self, event) -> None:
        self.controller.auto_backup_if_needed()
        self.controller.check_dirty_and_save()
        event.accept()

    def on_save_current_view(self) -> None:
        dialog = QInputDialog(self.gui)
        dialog.setWindowTitle("Save View")
        dialog.setLabelText("Enter view name:")
        dialog.setPalette(self.apply_theme())

        if dialog.exec_():
            name = dialog.textValue()
            if name:
                sort_column = (
                    self.table_view.horizontalHeader().sortIndicatorSection()
                )
                self.controller.save_current_view(
                    name=name,
                    custom_expr=self.gui.custom_filter_input.text(),
                    case_sensitive=self.gui.case_checkbox.isChecked(),
                    sort_column=sort_column,
                    field=self.gui.field_selector.currentText(),
                    operator=self.gui.operator_selector.currentText(),
                    value=self.gui.value_input.text(),
                    sort_key=self.gui.custom_sort_input.currentText(),
                    ascending=(
                        self.gui.sort_order_selector.currentText() == "Asc"
                    ),
                )
                self.view_selector_populate_set_to_default()
                self.gui.set_view_selector(name)

    def load_selected_view(self, view_name: str) -> None:
        # View
        cleaned_name = view_name.replace(" (default)", "")
        config, sort_column = self.controller.load_view_config(
            view_name=cleaned_name
        )
        if not config:
            return

        self.gui.load_selected_view(config)

        # Filter
        search_text: str = config.get("custom_filter", "")
        self.proxy_model.set_custom_filter_expression(search_text)
        self.proxy_model.set_filter_text(
            search_text if search_text.isalnum() else ""
        )
        filter_cfg = config.get("filter", {})
        self.proxy_model.set_structured_filter(
            filter_cfg.get("field", ""),
            filter_cfg.get("operator", "=="),
            filter_cfg.get("value", ""),
        )
        self.update_filter_operators()

        # Sort
        sort_expr = config.get("custom_sort_key", "").strip()
        self.proxy_model.set_custom_sort_key(sort_expr)
        self.proxy_model.rebuild_sort_key_cache()

        if sort_expr:
            sort_order = (
                Qt.AscendingOrder
                if config.get("ascending", True)
                else Qt.DescendingOrder
            )
            self.table_view.sortByColumn(sort_column, sort_order)
            self.table_view.horizontalHeader().setSortIndicatorShown(True)
            self.table_view.horizontalHeader().setSortIndicator(
                sort_column, sort_order
            )
        if not config.get("custom_sort_key", "").strip():
            self.on_clear_custom_sort()
            return

        # # 🛠 Force Apply Sort logic on startup
        # expr = self.gui.custom_sort_input.currentText().strip()
        # if expr:
        #     self.apply_custom_sort()
        # self.apply_custom_sort()

    def view_selector_populate_set_to_default(self) -> None:
        all_views = self.controller.get_all_view_names()
        default_name = self.controller.get_default_view_name()
        self.gui.refresh_view_selector(all_views, default_name)

    def apply_custom_sort(self) -> None:
        sort_key = self.gui.custom_sort_input.currentText().strip()
        ascending = self.gui.sort_order_selector.currentText() == "Asc"

        if sort_key and not sort_key.startswith("Enter Custom Sort"):
            # This fixes (somehow) the issue of the sorting sometimes
            # reverting to column 0 (id) even when there is a sort_key
            self.table_view.sortByColumn(0, Qt.AscendingOrder)

            self.proxy_model.set_custom_sort_key(sort_key)
            self.proxy_model.rebuild_sort_key_cache()

            # ✅ Visually apply saved sort direction (fallback)
            headers = self.controller.apply_custom_sort(
                self.proxy_model.sort_key_cache
            )
            sort_column = (
                headers.index("sort key") if "sort key" in headers else 0
            )
            sort_order = Qt.AscendingOrder if ascending else Qt.DescendingOrder
            self.table_view.sortByColumn(sort_column, sort_order)
            self.table_view.horizontalHeader().setSortIndicator(
                sort_column, sort_order
            )
            self.table_view.horizontalHeader().setSortIndicatorShown(True)

    def on_set_default_view(self) -> None:
        view_name = self.gui.get_current_view_name().replace(" (default)", "")
        self.controller.set_default_view(view_name)
        self.view_selector_populate_set_to_default()

    def update_custom_filter_expr(self) -> None:
        expr = self.gui.custom_filter_input.text()
        self.proxy_model.set_custom_filter_expression(expr)

        # Set search text ONLY if expression is a simple word
        if expr and (expr.isdigit() or expr.isalpha()):
            self.proxy_model.set_filter_text(expr)
            self.proxy_model.set_custom_filter_expression("")
        else:
            self.proxy_model.set_filter_text("")
            self.proxy_model.set_custom_filter_expression(expr)

    def update_filter_operators(self) -> None:
        field = self.controller.get_structured_filter_field()
        role = self.proxy_model.RAW_VALUE_ROLE
        sample_value = self.controller.update_filter_operators(field, role)
        self.gui.update_filter_operators(sample_value)

    def on_clear_filter(self) -> None:
        self.gui.set_filter_defaults()
        """Reset structured filter."""
        self.proxy_model.set_structured_filter("", "==", "")

    def on_clear_custom_sort(self) -> None:
        self.gui.set_sort_defaults()
        self.controller.clear_custom_sort()
        self.proxy_model.set_custom_sort_key("")
        self.proxy_model.sort_key_cache.clear()
        self.table_view.sortByColumn(0, Qt.AscendingOrder)

    def apply_theme(self) -> QPalette:
        is_dark = self.gui.theme_selector.currentText() == "Dark"
        self.controller.save_theme_to_config(is_dark)
        return self.gui.apply_theme()

    def apply_structured_filter(self) -> None:
        field = self.gui.field_selector.currentText()
        operator = self.gui.operator_selector.currentText()
        clean_value = self.gui.value_input.text()

        if not field or not operator:
            return

        """Apply structured field filter via proxy model."""
        ProxyModelService.apply_filter(
            self.proxy_model, field, operator, clean_value
        )

        # Reset sort to original order if no sort key is active
        if not self.proxy_model.custom_sort_key:
            self.table_view.horizontalHeader().setSortIndicator(
                -1, Qt.AscendingOrder
            )

        self.gui.on_apply_structured_filter()
        self.update_structured_filter(field, operator, clean_value)

        # Reset sort to original order if no sort key is active
        if not self.proxy_model.custom_sort_key:
            self.table_view.horizontalHeader().setSortIndicator(
                -1, Qt.AscendingOrder
            )

    def update_structured_filter(self, field: str, operator: str, value: str):
        self.proxy_model.set_structured_filter(field, operator, value)

    def clear_custom_filter(self):
        self.proxy_model.set_custom_filter_expression("")
        self.proxy_model.set_filter_text("")  # reset search text too
