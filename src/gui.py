# gui.py
import sys
import logging

from PyQt5.QtCore import Qt, QTimer, QDateTime
from PyQt5.QtWidgets import (
    QComboBox,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
    QInputDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QHBoxLayout,
    QShortcut,
    QTableView,
    QHeaderView,
)
from PyQt5.QtGui import QKeySequence, QPalette, QColor
from rich_text_delegate import RichTextDelegate

from filter_proxy import TableFilterProxyModel
from proxy_model_service import ProxyModelService
from workspace_controller import WorkspaceController
from utils import get_save_time_label_text
from version import __version__

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Main GUI for user interaction with saved data and IU configurations
    (profiles) & data configurations.
    """

    def __init__(self) -> None:
        """
        Initiates data manager for user to interact with data.

        Handles fresh start situation (no previously existing profiles)
        """
        super().__init__()
        self.setWindowTitle("Interactive Data Workspace")

        self.table_view = QTableView()
        # Enable text wrapping in the table view
        self.table_view.setTextElideMode(Qt.ElideNone)

        self.proxy_model = TableFilterProxyModel()
        self.controller = WorkspaceController()
        self.table_view.setModel(self.proxy_model)
        # Sorting only works through proxy
        self.table_view.setSortingEnabled(True)

        # Setup layout, widgets, etc.
        self.central_widget = QWidget()
        self.main_layout = QVBoxLayout()
        self.central_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.central_widget)

        self._init_ui()
        self._connect_signals()

        # Autosave timer
        self.auto_save_timer = QTimer(self)
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

        # Generates self.model but requires elements initiated
        # along with populated theme and profile selectors
        self.on_profile_changed()

    def _init_ui(self) -> None:
        # Profile selection dropdown
        self.profile_label = QLabel("Select Profile:")
        self.profile_selector = QComboBox()
        self.add_profile_button = QPushButton("Add Profile")
        self.update_profile_list()

        # Check if profiles exist, if not prompt user for a new one
        if not self.profile_selector.count():
            QTimer.singleShot(
                0, self.create_new_profile
            )  # defer profile creation

        # Save status
        self.save_label = QLabel("Last saved: just now")

        # Theme Selector
        self.theme_label = QLabel("Select Theme:")
        self.theme_selector = QComboBox()
        self.theme_selector.addItems(["Light", "Dark"])

        self.field_selector: QComboBox = QComboBox()
        self.custom_expr_input: QLineEdit = QLineEdit()
        self.operator_selector: QComboBox = QComboBox()
        self.value_input: QLineEdit = QLineEdit()
        self.custom_sort_input: QComboBox = QComboBox()
        self.sort_order_selector: QComboBox = QComboBox()
        self.undo_history_combo: QComboBox = QComboBox()
        self.redo_history_combo: QComboBox = QComboBox()

        # Data handling
        self.case_checkbox: QCheckBox = QCheckBox("Case Sensitive")
        self.case_checkbox.setChecked(False)

        # Save View Button
        self.save_view_button = QPushButton("Save Current View")

        # View Loader Dropdown
        self.view_selector: QComboBox = QComboBox()
        self.view_selector.setPlaceholderText("Load Saved View")
        # Populate view names at startup
        self.refresh_view_selector()

        # Default view button
        self.set_default_button = QPushButton("Set as Default View")

        # Filter
        self.field_selector.setPlaceholderText("Field")
        self.operator_selector.addItems(["==", "!=", ">", "<", ">=", "<="])
        self.value_input.setPlaceholderText("Value")

        self.structured_ok_button = QPushButton("OK")
        self.structured_ok_button.setFixedWidth(40)

        self.custom_expr_label = QLabel("Filter: ")
        self.custom_expr_input.setPlaceholderText(
            "Custom Filter Expression (e.g. status == 'active')"
        )

        self.clear_filter_button = QPushButton("Clear")
        self.clear_filter_button.setFixedWidth(50)

        self.custom_expr_help_button = QPushButton("?")
        self.custom_expr_help_button.setFixedWidth(25)

        # Custom sort
        self.custom_sort_input.setEditable(True)
        self.custom_sort_input.setInsertPolicy(QComboBox.InsertAtTop)
        # Insert a fake placeholder item
        placeholder = "Enter Custom Sort Key (e.g. len(name) + priority)"
        line_edit = self.custom_sort_input.lineEdit()
        line_edit.setPlaceholderText(placeholder)

        self.sort_label = QLabel("Sort: ")
        self.clear_sort_button = QPushButton("Clear")
        self.clear_sort_button.setFixedWidth(50)

        self.apply_sort_button = QPushButton("Apply Custom Sort")

        self.sort_order_selector.addItems(["Asc", "Desc"])

        self.custom_sort_help_button = QPushButton("?")
        self.custom_sort_help_button.setFixedWidth(25)

        # Undo/Redo history pulldown
        self.undo_history_combo.setPlaceholderText("Undo History")
        self.redo_history_combo.setPlaceholderText("Redo History")

        # Undo Redo
        # Add buttons:
        self.undo_button = QPushButton("Undo (Ctrl+Z)")
        self.redo_button = QPushButton("Redo (Ctrl+Y)")
        # Add to layout:
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.undo_button)
        button_layout.addWidget(self.redo_button)

        # Add to layout (next to undo/redo buttons):
        combo_layout = QHBoxLayout()
        combo_layout.addWidget(self.undo_history_combo)
        combo_layout.addWidget(self.redo_history_combo)

        # Apply the UI
        self.main_layout.addWidget(self.table_view)
        self.main_layout.addLayout(button_layout)
        self.main_layout.addLayout(combo_layout)
        profile_layout = QHBoxLayout()
        profile_layout.addWidget(self.add_profile_button)
        profile_layout.addWidget(self.profile_label)
        profile_layout.addWidget(self.profile_selector)
        self.main_layout.addLayout(profile_layout)
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(self.theme_label)
        theme_layout.addWidget(self.theme_selector)
        self.main_layout.addLayout(theme_layout)
        view_layout = QHBoxLayout()
        view_layout.addWidget(self.save_view_button)
        view_layout.addWidget(self.view_selector)
        view_layout.addWidget(self.set_default_button)
        self.main_layout.addLayout(view_layout)
        search_layout = QHBoxLayout()
        search_layout.addWidget(self.clear_filter_button)
        search_layout.addWidget(self.custom_expr_label)
        search_layout.addWidget(self.custom_expr_input)
        search_layout.addWidget(self.case_checkbox)
        search_layout.addWidget(self.custom_expr_help_button)
        self.main_layout.addLayout(search_layout)
        structured_layout = QHBoxLayout()
        structured_layout.addWidget(self.field_selector)
        structured_layout.addWidget(self.operator_selector)
        structured_layout.addWidget(self.value_input)
        structured_layout.addWidget(self.structured_ok_button)
        self.main_layout.addLayout(structured_layout)
        sort_layout = QHBoxLayout()
        sort_layout.addWidget(self.clear_sort_button)
        sort_layout.addWidget(self.sort_label)
        sort_layout.addWidget(self.custom_sort_input)
        sort_layout.addWidget(self.sort_order_selector)
        sort_layout.addWidget(self.apply_sort_button)
        sort_layout.addWidget(self.custom_sort_help_button)
        self.main_layout.addLayout(sort_layout)
        self.main_layout.addWidget(self.save_label)

        # Footer layout for version info
        footer_layout = QHBoxLayout()
        self.version_label = QLabel(f"v{__version__} running")
        self.version_label.setStyleSheet("color: gray; font-size: 10px;")
        footer_layout.addWidget(self.version_label)
        footer_layout.addStretch()  # Push label to the left or right

        # Add to main layout
        self.main_layout.addLayout(footer_layout)

    def _connect_signals(self) -> None:
        """
        Connects signals to their respective slots.
        """
        self.profile_selector.currentIndexChanged.connect(
            self.on_profile_changed
        )
        self.theme_selector.currentIndexChanged.connect(
            lambda: self.setPalette(self.apply_theme())
        )
        self.add_profile_button.clicked.connect(self.create_new_profile)

        # Connect apply custom sort button
        self.apply_sort_button.clicked.connect(self.apply_custom_sort)

        # Connect structured filter OK button
        self.structured_ok_button.clicked.connect(
            self.on_apply_structured_filter
        )

        # Connect clear filter button
        self.clear_filter_button.clicked.connect(
            self.on_clear_structured_filter
        )

        # Connect custom expression help button
        self.custom_expr_help_button.clicked.connect(
            self.show_filter_expr_help
        )

        # Connect custom sort help button
        self.custom_sort_help_button.clicked.connect(self.show_sort_expr_help)

        # Data handling
        self.case_checkbox.stateChanged.connect(
            lambda state: self.proxy_model.set_case_sensitive(
                state == Qt.Checked
            )
        )

        # Save view button
        self.save_view_button.clicked.connect(self.on_save_current_view)

        # View loader dropdown
        self.view_selector.activated[str].connect(self.load_selected_view)

        # Default view button
        self.set_default_button.clicked.connect(self.on_set_default_view)

        # Filter
        self.field_selector.currentTextChanged.connect(
            self.update_filter_operators
        )

        self.custom_expr_input.textChanged.connect(
            self.update_custom_filter_expr
        )

        # Sort
        self.clear_sort_button.clicked.connect(self.clear_custom_sort)

        # Undo redo
        self.undo_button.clicked.connect(self.controller.undo)
        self.redo_button.clicked.connect(self.controller.redo)

        # Add shortcuts:
        undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self)
        redo_shortcut = QShortcut(QKeySequence("Ctrl+Y"), self)
        undo_shortcut.activated.connect(self.controller.undo)
        redo_shortcut.activated.connect(self.controller.redo)

    def update_save_label(self) -> None:
        text = get_save_time_label_text(self.last_save_time)
        self.save_label.setText(text)

    def on_profile_changed(self) -> None:
        current_profile = self.profile_selector.currentText()
        config = self.controller.load_profile(current_profile)
        if not config:
            return
        model, headers = self.controller.load_data(self.proxy_model)
        self.proxy_model.setSourceModel(model)

        # Connect to model update
        model.stack_changed.connect(
            lambda: self.update_undo_redo_history(
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

        self.theme_selector.setCurrentText(
            "Dark" if config.is_dark_mode() else "Light"
        )
        self.setPalette(self.apply_theme())

        self.field_selector.clear()
        self.field_selector.addItems(headers)
        self.update_filter_operators()  # Run after headers added

        self.refresh_view_selector()  # make sure the dropdown is populated

        default_view = self.controller.get_default_view()
        if default_view:
            self.load_selected_view(default_view)

            # 🛠 Force Apply Sort logic on startup
            expr = self.custom_sort_input.currentText().strip()
            if expr:
                self.apply_custom_sort()
            index = self.view_selector.findText(f"{default_view} (default)")
            if index != -1:
                self.view_selector.setCurrentIndex(index)
        else:
            self.on_clear_structured_filter()
            self.clear_custom_sort()

        # Clear history dropdowns
        self.undo_history_combo.clear()
        self.redo_history_combo.clear()

        logger.info(f"Switched to profile: {current_profile}")

    def apply_theme(self) -> QPalette:
        """
        Applies the current user's theme settings.
        """
        is_dark = self.theme_selector.currentText() == "Dark"
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

    def create_new_profile(self) -> None:
        """
        Prompts the user to enter a new profile name
        """
        dialog = QInputDialog(self)
        dialog.setPalette(self.apply_theme())
        new_profile, ok = dialog.getText(
            self, "New Profile", "Enter profile name:"
        )
        if ok and new_profile and not new_profile.strip() == "":
            created = self.controller.create_profile(new_profile)
            if created:
                self.update_profile_list()
                index = self.profile_selector.findText(new_profile)
                if index != -1:
                    self.profile_selector.setCurrentIndex(index)
                logger.info(f"New profile created for {new_profile}")
            else:
                QMessageBox.warning(
                    self,
                    "Profile Exists",
                    f"The profile '{new_profile}' already exists.",
                )

        if not self.profile_selector.count():
            sys.exit(
                "No profiles available. Please create a new "
                + "profile to continue."
            )

    def update_profile_list(self) -> None:
        """
        Refresh the profile list from existing config files.
        """
        self.profile_selector.clear()
        self.profile_selector.addItems(self.controller.get_profiles())

    def update_undo_redo_history(
        self, undo_stack: list, redo_stack: list
    ) -> None:
        self.undo_history_combo.clear()
        self.redo_history_combo.clear()
        for action in reversed(undo_stack):
            self.undo_history_combo.addItem(action.description())
        for action in reversed(redo_stack):
            self.redo_history_combo.addItem(action.description())

    def closeEvent(self, event) -> None:
        self.controller.auto_backup_if_needed()
        self.controller.check_dirty_and_save()
        event.accept()

    def on_save_current_view(self) -> None:
        dialog = QInputDialog(self)
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
                    custom_expr=self.custom_expr_input.text(),
                    case_sensitive=self.case_checkbox.isChecked(),
                    sort_column=sort_column,
                    field=self.field_selector.currentText(),
                    operator=self.operator_selector.currentText(),
                    value=self.value_input.text(),
                    sort_key=self.custom_sort_input.currentText(),
                    ascending=(
                        self.sort_order_selector.currentText() == "Asc"
                    ),
                )
                self.refresh_view_selector()
                index = self.view_selector.findText(name)
                if index != -1:
                    self.view_selector.setCurrentIndex(index)

    def load_selected_view(self, view_name: str) -> None:
        cleaned_name = view_name.replace(" (default)", "")
        config, sort_column = self.controller.load_view_config(
            view_name=cleaned_name
        )
        if not config:
            return

        search_text: str = config.get("search_text", "")
        self.proxy_model.set_custom_filter_expression(search_text)
        self.proxy_model.set_search_text(
            search_text if search_text.isalnum() else ""
        )
        filter_cfg = config.get("filter", {})
        self.proxy_model.set_structured_filter(
            filter_cfg.get("field", ""),
            filter_cfg.get("operator", "=="),
            filter_cfg.get("value", ""),
        )
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

        # TODO: self.custom_expr_input.setText(config.get("search_text", ""))
        self.custom_expr_input.setText(config.get("custom_filter", ""))
        self.case_checkbox.setChecked(config.get("case_sensitive", False))

        filter_config = config.get("filter", {})
        self.operator_selector.setCurrentText(
            filter_config.get("operator", "==")
        )
        self.field_selector.setCurrentText(filter_config.get("field", ""))
        self.value_input.setText(filter_config.get("value", ""))

        self.update_filter_operators()

        self.refresh_view_selector()
        if not config.get("custom_sort_key", "").strip():
            self.clear_custom_sort()
            return

        self.sort_order_selector.setCurrentText(
            "Asc" if config.get("ascending", True) else "Desc"
        )
        self.custom_sort_input.setCurrentText(
            config.get("custom_sort_key", "")
        )
        self.apply_custom_sort()

    def refresh_view_selector(self) -> None:
        all_views = self.controller.get_all_view_names()
        default_name = self.controller.get_default_view_name()

        self.view_selector.clear()
        for name in all_views:
            label = f"{name} (default)" if name == default_name else name
            self.view_selector.addItem(label)

        if not default_name:
            return

        # ✅ Mark selection in dropdown
        for view_index in range(self.view_selector.count()):
            name = self.view_selector.itemText(view_index)
            if default_name in name:
                self.view_selector.setCurrentIndex(view_index)
                break

    def apply_custom_sort(self) -> None:
        sort_key = self.custom_sort_input.currentText().strip()
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
            ascending = self.sort_order_selector.currentText() == "Asc"
            sort_order = Qt.AscendingOrder if ascending else Qt.DescendingOrder
            self.table_view.sortByColumn(sort_column, sort_order)
            self.table_view.horizontalHeader().setSortIndicator(
                sort_column, sort_order
            )
            self.table_view.horizontalHeader().setSortIndicatorShown(True)

            # # This sets sort column and triggers ascending sort
            # # Which activates proxy's lessThan()
            # if self.custom_sort_input.findText(sort_key) == -1:
            #     self.custom_sort_input.insertItem(0, sort_key)

    def on_set_default_view(self) -> None:
        view_name = self.view_selector.currentText().replace(" (default)", "")
        self.controller.set_default_view(view_name)
        self.refresh_view_selector()
        # Ensure the current selection stays highlighted
        index = self.view_selector.findText(f"{view_name} (default)")
        if index != -1:
            self.view_selector.setCurrentIndex(index)

    def update_custom_filter_expr(self, expr: str) -> None:
        expr = self.custom_expr_input.text()

        self.proxy_model.set_custom_filter_expression(expr)

        # Set search text ONLY if expression is a simple word
        if expr and (expr.isdigit() or expr.isalpha()):
            self.proxy_model.set_search_text(expr)
            self.proxy_model.set_custom_filter_expression("")
        else:
            self.proxy_model.set_search_text("")
            self.proxy_model.set_custom_filter_expression(expr)

    def update_filter_operators(self) -> None:
        field = self.field_selector.currentText()
        role = self.proxy_model.RAW_VALUE_ROLE

        sample_value = self.controller.update_filter_operators(field, role)

        self.operator_selector.clear()

        if isinstance(sample_value, (int, float)):
            self.operator_selector.addItems(["==", "!=", "<", "<=", ">", ">="])
        elif isinstance(sample_value, bool):
            self.operator_selector.addItems(["==", "!="])
        elif isinstance(sample_value, str) or sample_value is None:
            # Default to string if unknown
            self.operator_selector.addItems(
                ["contains", "startswith", "endswith", "matches", "not"]
            )
        else:
            self.operator_selector.addItems(["==", "!="])  # fallback

    def show_filter_expr_help(self) -> None:
        msg = QMessageBox(self)
        msg.setWindowTitle("Custom Filter Expression Help")
        msg.setText(
            "Examples:\n"
            "  status == 'active'\n"
            "  priority >= 3 and 'urgent' in tags\n"
            "  name.startswith('A')\n\n"
            "You can use:\n"
            "  - len(x)\n"
            "  - str(), int(), float()\n"
            "  - min(), max(), round()\n\n"
            "Operators: ==, !=, <, >, <=, >=, in, and, or, not\n\n"
            "Field names (columns) are available as variables.\n"
            "For example, use 'priority', 'status', 'tags', 'name', etc."
        )
        msg.setIcon(QMessageBox.NoIcon)  # <- No chime!
        msg.exec_()

    def show_sort_expr_help(self) -> None:
        msg = QMessageBox(self)
        msg.setWindowTitle("Custom Sort Key Help")
        msg.setText(
            "Examples of custom sort key expressions:\n\n"
            "- age\n"
            "- len(name)\n"
            "- len(tags)\n"
            "- email.split('@')[-1]\n"
            "- name.lower()\n"
            "- 'admin' in tags\n\n"
            "You can use:\n"
            "- len(), str.lower(), str.split(), basic math (+ - * /)\n"
            "- Boolean logic: and, or, not\n"
            "- Access list/dict fields like tags or preferences"
            "['notifications']"
        )
        msg.setIcon(QMessageBox.NoIcon)  # <- No chime!
        msg.exec_()

    def on_apply_structured_filter(self) -> None:
        field = self.field_selector.currentText()
        operator = self.operator_selector.currentText()
        clean_value = self.value_input.text()

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
        # Auto-quote strings if needed
        if (
            operator
            in ["contains", "startswith", "endswith", "matches", "not"]
            or not clean_value.isnumeric()
        ):
            value = f"'{clean_value}'"
        else:
            value = clean_value

        match operator:
            case "contains":
                expr = f"{clean_value} in {field}"
            case "not":
                expr = f"{clean_value} not in {field}"
            case "matches":
                expr = f"{clean_value} in {field}"
            case "startswith":
                expr = f"{field}.startswith({value})"
            case "endswith":
                expr = f"{field}.endswith({value})"
            case _:
                expr = f"{field} {operator} {value}"

        # ➡️ Append to existing custom expression if present
        current_expr = self.custom_expr_input.text().strip()

        if current_expr:
            combined_expr = f"{current_expr} and {expr}"
        else:
            combined_expr = expr

        self.custom_expr_input.setText(combined_expr)

        # self.controller.apply_structured_filter(combined_expr)

        # ✅ CLEAR structured fields after inserting
        self.field_selector.setCurrentIndex(-1)
        self.operator_selector.clear()
        self.value_input.clear()

    def on_clear_structured_filter(self) -> None:
        self.custom_expr_input.clear()
        """Reset structured filter."""
        self.proxy_model.set_structured_filter("", "==", "")

    def clear_custom_sort(self) -> None:
        self.custom_sort_input.setCurrentText("")
        self.controller.clear_custom_sort()
        self.sort_order_selector.setCurrentText("Asc")
        self.proxy_model.set_custom_sort_key("")
        self.proxy_model.sort_key_cache.clear()
        self.table_view.sortByColumn(0, Qt.AscendingOrder)
