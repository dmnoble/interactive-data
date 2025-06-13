from filter_proxy import TableFilterProxyModel
from workspace_controller import WorkspaceController
from gui import BuildGui
from utils import get_save_time_label_text

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
from PyQt5.QtGui import QKeySequence, QPalette, QColor
from PyQt5.QtCore import Qt, QTimer, QDateTime

logger = logging.getLogger(__name__)


class GuiPresenter:
    def __init__(
        self,
        controller: WorkspaceController,
        gui: BuildGui,
        table_view: QTableView,
    ) -> None:
        self.controller = controller
        self.gui = gui
        self.proxy_model = TableFilterProxyModel()

        self.setup_table_view(table_view)
        self.set_auto_saves()

        self.setup_bindings()
        self.connect_signals()

        # Check if profiles exist, if not prompt user for a new one
        if not self.controller.get_profiles():
            self.create_new_profile()
        else:
            self.gui.profile_selector.addItems(self.controller.get_profiles())

    # def closeEvent(self, event) -> None:
    #     self.controller.auto_backup_if_needed()
    #     self.controller.check_dirty_and_save()
    #     event.accept()

    def setup_table_view(self, table_view: QTableView):
        self.table_view: QTableView = table_view
        self.table_view.setModel(self.proxy_model)
        self.table_view.setItemDelegate(RichTextDelegate())
        self.table_view.setSortingEnabled(True)
        self.table_view.setWordWrap(False)
        self.table_view.setTextElideMode(Qt.ElideRight)

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

    def view_selector_populate_set_to_default(self) -> None:
        all_views = self.controller.get_all_view_names()
        default_name = self.controller.get_default_view_name()
        self.gui.refresh_view_selector(all_views, default_name)

    # === View/profile loading helpers ===
    def setup_bindings(self):
        self.controller.profileNameChanged.connect(self.on_profile_changed)

        self.controller.viewNameChanged.connect(self.on_view_changed)

        self.proxy_model.sortKeyChanged.connect(self.apply_sort_key)

        self.proxy_model.filterExprChanged.connect(self.apply_filter_expr)

        self.proxy_model.filterCaseChanged.connect(
            lambda state: self.gui.case_checkbox.setChecked(state)
        )

    def on_view_changed(self) -> None:
        self.gui.sort_order_selector.setCurrentText(
            "Asc" if self.controller.get_sort_order() else "Desc"
        )
        # Filter
        self.proxy_model.set_case_sensitive(
            self.controller.get_filter_case_sensitive()
        )
        filter_text: str = self.controller.get_custom_filter()
        self.proxy_model.set_filter_expression(filter_text)
        self.update_filter_operators()
        # Sort
        sort_expr = self.controller.get_custom_sort()
        self.proxy_model.set_custom_sort_key(sort_expr)

    def apply_sort_key(self, sort_key: str) -> None:
        if not sort_key or sort_key.startswith("Enter Custom Sort"):
            self.gui.set_sort_defaults()
            self.controller.clear_custom_sort()
            self.table_view.sortByColumn(0, Qt.AscendingOrder)
            return

        self.gui.custom_sort_input.setCurrentText(sort_key)

        # This fixes (somehow) the issue of the sorting sometimes
        # reverting to column 0 (id) even when there is a sort_key
        self.table_view.sortByColumn(0, Qt.AscendingOrder)

        # ✅ Visually apply saved sort direction (fallback)
        headers = self.controller.apply_custom_sort(
            self.proxy_model.sort_key_cache
        )
        sort_column = headers.index("sort key") if "sort key" in headers else 0

        ascending = self.gui.sort_order_selector.currentText() == "Asc"
        sort_order = Qt.AscendingOrder if ascending else Qt.DescendingOrder

        self.table_view.sortByColumn(sort_column, sort_order)
        self.table_view.horizontalHeader().setSortIndicator(
            sort_column, sort_order
        )
        self.table_view.horizontalHeader().setSortIndicatorShown(True)

    def apply_filter_expr(self, expr: str) -> None:
        if expr is None or expr.startswith("Enter Custom Filter"):
            self.gui.set_filter_defaults()
        else:
            self.gui.custom_filter_input.setText(expr)

        # Reset sort to original order if no sort key is active
        if not self.proxy_model.custom_sort_key:
            self.table_view.horizontalHeader().setSortIndicator(
                -1, Qt.AscendingOrder
            )

    def on_profile_changed(self) -> None:
        # self.gui.update_profile_list(self.controller.get_profiles())

        new_profile = self.controller.profile_name
        index = self.gui.profile_selector.findText(new_profile)
        if index != -1:
            self.gui.profile_selector.setCurrentIndex(index)

        if not self.controller.profile_config:
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
            "Dark"
            if self.controller.profile_config.is_dark_mode()
            else "Light"
        )
        self.gui.setPalette(self.apply_theme())

        self.gui.field_selector.clear()
        self.gui.field_selector.addItems(headers)
        self.update_filter_operators()  # Run after headers added

        # make sure the dropdown is populated
        self.view_selector_populate_set_to_default()

        default_view = self.controller.get_default_view()
        if default_view:
            self.controller.load_view_config(default_view)
        else:
            self.proxy_model.set_filter_expression("")
            self.proxy_model.set_custom_sort_key("")

        # Clear history dropdowns
        self.gui.undo_history_combo.clear()
        self.gui.redo_history_combo.clear()

    def apply_theme(self) -> QPalette:
        """
        Applies the current user's theme settings.
        """
        is_dark = self.gui.theme_selector.currentText() == "Dark"
        self.controller.save_theme_to_config(is_dark)

        if is_dark:
            palette = QPalette()
            palette.setColor(QPalette.Window, QColor(53, 53, 53))
            palette.setColor(QPalette.WindowText, Qt.white)
            palette.setColor(QPalette.Base, QColor(25, 25, 25))
            palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
            palette.setColor(QPalette.ToolTipBase, Qt.black)
            palette.setColor(QPalette.ToolTipText, Qt.white)
            palette.setColor(QPalette.Text, Qt.white)
            palette.setColor(QPalette.Button, QColor(53, 53, 53))
            palette.setColor(QPalette.ButtonText, Qt.white)
            palette.setColor(QPalette.BrightText, Qt.red)
            palette.setColor(QPalette.Link, QColor(42, 130, 218))
            palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            palette.setColor(QPalette.HighlightedText, Qt.black)
            return palette
        else:
            return QPalette()  # Reset to default light theme

    # === GUI initiated slots ===
    def connect_signals(self) -> None:
        """
        Connects signals to their respective slots.
        """
        self.gui.profile_selector.currentIndexChanged.connect(
            lambda index: self.controller.load_profile(
                self.gui.profile_selector.currentText() if index >= 0 else ""
            )
        )
        self.gui.add_profile_button.clicked.connect(self.create_new_profile)

        self.gui.theme_selector.currentIndexChanged.connect(
            lambda: self.gui.setPalette(self.apply_theme())
        )

        # Save view button
        self.gui.save_view_button.clicked.connect(self.on_save_current_view)

        # View loader dropdown
        self.gui.view_selector.activated[str].connect(
            lambda view_name: self.controller.load_view_config(view_name)
        )

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
            lambda: self.proxy_model.set_filter_expression(
                self.gui.custom_filter_input.text()
            )
        )
        self.gui.case_checkbox.stateChanged.connect(
            lambda state: self.proxy_model.set_case_sensitive(
                state == Qt.Checked
            )
        )
        # Connect clear filter button
        self.gui.clear_filter_button.clicked.connect(
            lambda: self.proxy_model.set_filter_expression("")
        )

        # Sort
        self.gui.apply_sort_button.clicked.connect(
            lambda: self.proxy_model.set_custom_sort_key(
                self.gui.custom_sort_input.currentText()
            )
        )
        self.gui.clear_sort_button.clicked.connect(
            lambda: self.proxy_model.set_custom_sort_key("")
        )

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
        self.gui.save_label.setText(text)

    def update_filter_operators(self) -> None:
        field = self.gui.field_selector.currentText()
        role = self.proxy_model.RAW_VALUE_ROLE
        sample_value = self.controller.update_filter_operators(field, role)
        self.gui.update_filter_operators(sample_value)

    def apply_structured_filter(self) -> None:
        self.gui.on_apply_structured_filter()
        self.proxy_model.set_filter_expression(
            self.gui.custom_filter_input.text()
        )

    def create_new_profile(self) -> None:
        """
        Prompts the user to enter a new profile name
        """
        dialog = QInputDialog(self.gui)
        if self.controller.profile_config:
            dialog.setPalette(self.apply_theme())
        new_profile, ok = dialog.getText(
            self.gui, "New Profile", "Enter profile name:"
        )
        if ok and new_profile and not new_profile.strip() == "":
            created = self.controller.create_profile(new_profile)
            if created:
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
                    custom_expr=self.proxy_model.filter_expr,
                    case_sensitive=self.proxy_model.case_sensitive,
                    sort_column=sort_column,
                    sort_key=self.proxy_model.custom_sort_key,
                    ascending=(
                        self.gui.sort_order_selector.currentText() == "Asc"
                    ),
                )
                self.gui.set_view_selector(name)

    def on_set_default_view(self) -> None:
        view_name = self.gui.get_current_view_name().replace(" (default)", "")
        self.controller.set_default_view(view_name)
        self.view_selector_populate_set_to_default()
