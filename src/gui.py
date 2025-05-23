# gui.py
import sys
from PyQt5.QtWidgets import (
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QComboBox,
    QLabel,
    QLineEdit,
    QInputDialog,
    QHBoxLayout,
    QShortcut,
    QCheckBox,
    QApplication,
    QMessageBox,
)
from PyQt5.QtCore import Qt, QDateTime, QTimer
from PyQt5.QtGui import QPalette, QColor, QKeySequence
from logger import setup_logger
from utils import get_save_time_label_text
from view_config import (
    get_all_view_names,
    get_default_view_name,
)
from workspace_controller import WorkspaceController

logger = setup_logger("gui")


class MainWindow(QMainWindow):
    """
    Main GUI for user interaction with saved data and IU configurations
    (profiles) & data configurations.


    Attributes:
        data_manager (Data_Manager): controls how data is saved and loaded.
    """

    current_profile = ""

    def __init__(self, data_manager, version: str):
        """
        Initiates data manager for user to interact with data.

        Handles fresh start situation (no previously existing profiles)

        Supplies user capabilities:
            -   UI configuration (profiles), including selecting, loading, and
            saving
            -   Data handling such as displaying, filtering, sorting
        """
        super().__init__()
        self.setWindowTitle("Data Manager App")

        self.data_manager = data_manager
        self.controller = WorkspaceController()

        # Auto-Save Logic
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(
            self.controller.check_dirty_and_save
        )
        self.auto_save_timer.start(5 * 60 * 1000)  # Every 5 minutes

        # GUI label for time since last save
        self.last_save_time = QDateTime.currentDateTime()
        self.save_label = QLabel("Last saved: just now")
        self.save_timer = QTimer()
        self.save_timer.timeout.connect(self.update_save_label)
        self.save_timer.start(60 * 1000)  # every minute

        # Timer for the hourly backup
        self.backup_timer = QTimer()
        self.backup_timer.timeout.connect(
            self.controller.auto_backup_if_needed
        )
        self.backup_timer.start(60 * 60 * 1000)  # every hour in ms

        # Profile selection dropdown
        self.profile_label = QLabel("Select Profile:")
        self.profile_selector = QComboBox()
        self.update_profile_list()
        self.add_profile_button = QPushButton("Add Profile")
        self.add_profile_button.clicked.connect(self.create_new_profile)

        # Check if profiles exist, if not prompt user for a new one
        if not self.profile_selector.count():
            self.create_new_profile()

        # Connect profile selection change
        self.profile_selector.currentIndexChanged.connect(
            self.on_profile_changed
        )

        # Theme Selector
        self.theme_label = QLabel("Select Theme:")
        self.theme_selector = QComboBox()
        self.theme_selector.addItems(["Light", "Dark"])
        self.theme_selector.currentIndexChanged.connect(self.apply_theme)

        self.view_selector: QComboBox = QComboBox()
        self.field_selector: QComboBox = QComboBox()
        self.custom_expr_input = QLineEdit()
        self.case_checkbox = QCheckBox("Case Sensitive")
        self.operator_selector = QComboBox()
        self.value_input: QLineEdit = QLineEdit()
        self.custom_sort_input = QComboBox()
        self.sort_order_selector = QComboBox()
        self.undo_history_combo = QComboBox()
        self.redo_history_combo = QComboBox()

        # Generates self.model but requires elements initiated
        # along with populated theme and profile selectors
        self.on_profile_changed()
        self.main_layout = QVBoxLayout()

        # Data handling
        self.case_checkbox.setChecked(False)
        self.case_checkbox.stateChanged.connect(
            lambda state: self.controller.set_case_sensitive(  # type: ignore
                state == Qt.Checked  # type: ignore
            )
        )

        # Save View Button
        self.save_view_button = QPushButton("Save Current View")
        self.save_view_button.clicked.connect(self.on_save_current_view)

        # View Loader Dropdown
        self.view_selector.setPlaceholderText("Load Saved View")
        self.view_selector.activated[str].connect(self.load_selected_view)
        # Populate view names at startup
        self.refresh_view_selector()

        # Default view button
        self.set_default_button = QPushButton("Set as Default View")
        self.set_default_button.clicked.connect(self.on_set_default_view)

        # Filter
        self.field_selector.setPlaceholderText("Field")
        self.field_selector.currentTextChanged.connect(
            self.update_filter_operators
        )
        self.operator_selector.addItems(["==", "!=", ">", "<", ">=", "<="])
        self.operator_selector.currentTextChanged.connect(
            lambda: self.controller.update_structured_filter(
                field=self.field_selector.currentText(),
                operator=self.operator_selector.currentText(),
                value=self.value_input.text(),
            )
        )
        self.value_input.setPlaceholderText("Value")
        self.value_input.textChanged.connect(
            lambda: self.controller.update_structured_filter(
                field=self.field_selector.currentText(),
                operator=self.operator_selector.currentText(),
                value=self.value_input.text(),
            )
        )

        self.structured_ok_button = QPushButton("OK")
        self.structured_ok_button.setFixedWidth(40)
        self.structured_ok_button.clicked.connect(
            self.on_apply_structured_filter
        )

        self.custom_expr_label = QLabel("Filter: ")
        self.custom_expr_input.setPlaceholderText(
            "Custom Filter Expression (e.g. status == 'active')"
        )
        self.custom_expr_input.textChanged.connect(
            lambda: self.controller.update_custom_filter_expr(
                self.custom_expr_input.text()
            )
        )

        self.clear_filter_button = QPushButton("Clear")
        self.clear_filter_button.setFixedWidth(50)
        self.clear_filter_button.clicked.connect(
            self.on_clear_structured_filter
        )

        self.custom_expr_help_button = QPushButton("?")
        self.custom_expr_help_button.setFixedWidth(25)
        self.custom_expr_help_button.clicked.connect(
            self.show_filter_expr_help
        )

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
        self.clear_sort_button.clicked.connect(self.clear_custom_sort)

        self.apply_sort_button = QPushButton("Apply Custom Sort")
        self.apply_sort_button.clicked.connect(self.apply_custom_sort)

        self.sort_order_selector.addItems(["Asc", "Desc"])

        self.custom_sort_help_button = QPushButton("?")
        self.custom_sort_help_button.setFixedWidth(25)
        self.custom_sort_help_button.clicked.connect(self.show_sort_expr_help)

        # Undo/Redo history pulldown
        self.undo_history_combo.setPlaceholderText("Undo History")
        self.redo_history_combo.setPlaceholderText("Redo History")

        # Undo Redo
        # Add buttons:
        self.undo_button = QPushButton("Undo (Ctrl+Z)")
        self.redo_button = QPushButton("Redo (Ctrl+Y)")
        self.undo_button.clicked.connect(self.controller.undo)
        self.redo_button.clicked.connect(self.controller.redo)

        # Add to layout:
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.undo_button)
        button_layout.addWidget(self.redo_button)

        # Add shortcuts:
        undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self)
        redo_shortcut = QShortcut(QKeySequence("Ctrl+Y"), self)
        undo_shortcut.activated.connect(self.controller.undo)
        redo_shortcut.activated.connect(self.controller.redo)

        # Add to layout (next to undo/redo buttons):
        combo_layout = QHBoxLayout()
        combo_layout.addWidget(self.undo_history_combo)
        combo_layout.addWidget(self.redo_history_combo)

        # Apply the UI
        self.main_layout.addWidget(self.controller.table_view)
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
        self.version_label = QLabel(f"v{version} running")
        self.version_label.setStyleSheet("color: gray; font-size: 10px;")
        footer_layout.addWidget(self.version_label)
        footer_layout.addStretch()  # Push label to the left or right

        # Add to main layout
        self.main_layout.addLayout(footer_layout)

        container = QWidget()
        container.setLayout(self.main_layout)
        self.setCentralWidget(container)

    def update_save_label(self):
        self.save_label.setText(get_save_time_label_text(self.last_save_time))

    def on_profile_changed(self):
        if self.current_profile == self.profile_selector.currentText():
            return
        self.current_profile = self.profile_selector.currentText()
        config = self.controller.load_profile(self.current_profile)
        headers = self.controller.load_data(self.update_undo_redo_history)

        self.controller.apply_to_view()
        self.update_save_label()

        if self.theme_selector:
            self.theme_selector.setCurrentText(
                "Dark" if config.is_dark_mode() else "Light"
            )
        self.apply_theme()

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

        print(f"Switched to profile: {self.current_profile}")

    def apply_theme(self):
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
            self.setPalette(palette)
        else:
            self.setPalette(QPalette())  # Reset to default light theme

    def create_new_profile(self):
        """
        Prompts the user to enter a new profile name upon a fresh start.
        """
        new_profile, ok = QInputDialog.getText(
            self, "New Profile", "Enter profile name:"
        )
        if ok and new_profile and not new_profile.strip() == "":
            self.controller.load_profile(
                new_profile
            )  # Create default config for the new profile
            self.update_profile_list()
            logger.info(f"New profile created for {new_profile}")
            self.profile_selector.setCurrentText(new_profile)
        else:
            sys.exit()

    def update_profile_list(self):
        """
        Refresh the profile list from existing config files.
        """
        self.profile_selector.clear()
        self.profile_selector.addItems(self.controller.get_profiles())

    def update_undo_redo_history(self, undo_stack, redo_stack):
        self.undo_history_combo.clear()
        self.redo_history_combo.clear()
        for action in reversed(undo_stack):
            self.undo_history_combo.addItem(action.description())
        for action in reversed(redo_stack):
            self.redo_history_combo.addItem(action.description())

    def closeEvent(self, event):
        self.controller.auto_backup_if_needed()
        self.controller.check_dirty_and_save()
        event.accept()

    def on_save_current_view(self):
        dialog = QInputDialog(self)
        dialog.setWindowTitle("Save View")
        dialog.setLabelText("Enter view name:")

        is_dark = self.theme_selector.currentText() == "Dark"
        if is_dark:
            dark_palette = QPalette()
            dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.WindowText, Qt.white)
            dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
            dark_palette.setColor(QPalette.Text, Qt.white)
            dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ButtonText, Qt.white)
            dialog.setPalette(dark_palette)
        else:
            dialog.setPalette(QApplication.palette())

        if dialog.exec_():
            name = dialog.textValue()
            if name:
                self.controller.save_current_view(
                    name=name,
                    custom_expr=self.custom_expr_input.text(),
                    case_sensitive=self.case_checkbox.isChecked(),
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

    def load_selected_view(self, name: str):
        cleaned_name, config = self.controller.load_view_config(
            view_name=name,
        )
        if not config:
            return

        self.custom_expr_input.setText(config.get("search_text", ""))
        self.case_checkbox.setChecked(config.get("case_sensitive", False))
        filter_config = config.get("filter", {})
        self.update_filter_operators()
        self.operator_selector.setCurrentText(
            filter_config.get("operator", "==")
        )
        self.field_selector.setCurrentText(filter_config.get("field", ""))
        self.value_input.setText(filter_config.get("value", ""))
        self.custom_expr_input.setText(config.get("custom_filter", ""))

        if not config.get("custom_sort_key", "").strip():
            self.clear_custom_sort()

        self.custom_sort_input.setCurrentText(
            config.get("custom_sort_key", "")
        )

        if config.get("ascending", True):
            self.sort_order_selector.setCurrentText("Asc")
        else:
            self.sort_order_selector.setCurrentText("Desc")

        self.apply_custom_sort()

        # ✅ Mark selection in dropdown
        for i in range(self.view_selector.count()):
            name = self.view_selector.itemText(i)
            if cleaned_name in name:
                self.view_selector.setCurrentIndex(i)
                break

    def refresh_view_selector(self):
        all_views = get_all_view_names(self.current_profile)
        default_name = get_default_view_name(self.current_profile)

        self.view_selector.clear()
        for name in all_views:
            label = f"{name} (default)" if name == default_name else name
            self.view_selector.addItem(label)

    def apply_custom_sort(self):
        asc = self.sort_order_selector.currentText() == "Asc"
        expr = self.custom_sort_input.currentText().strip()

        # Skip placeholder
        if not expr or expr.startswith("Enter Custom Sort"):
            return

        # This sets sort column and triggers ascending sort
        # Which activates proxy's lessThan()
        if self.custom_sort_input.findText(expr) == -1:
            self.custom_sort_input.insertItem(0, expr)

        self.controller.apply_custom_sort(
            sort_key=expr,
            ascending=asc,
        )

    def on_set_default_view(self):
        view_name = self.view_selector.currentText().replace(" (default)", "")
        self.controller.set_default_view(view_name)
        self.refresh_view_selector()
        # Ensure the current selection stays highlighted
        index = self.view_selector.findText(f"{view_name} (default)")
        if index != -1:
            self.view_selector.setCurrentIndex(index)

    def update_filter_operators(self):
        field = self.field_selector.currentText()

        sample_value = self.controller.update_filter_operators(field)

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

    def show_filter_expr_help(self):
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

    def show_sort_expr_help(self):
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

    def on_apply_structured_filter(self):
        field = self.field_selector.currentText()
        operator = self.operator_selector.currentText()
        clean_value = self.value_input.text()

        if not field or not operator:
            return

        self.controller.apply_structured_filter(
            field,
            operator=operator,
            value=clean_value,
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

        if operator == "contains":
            expr = f"{clean_value} in {field}"
        elif operator == "not":
            expr = f"{clean_value} not in {field}"
        elif operator == "matches":
            expr = f"{clean_value} in {field}"  # simple version
        elif operator == "startswith":
            expr = f"{field}.startswith({value})"
        elif operator == "endswith":
            expr = f"{field}.endswith({value})"
        else:
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

    def on_clear_structured_filter(self):
        self.custom_expr_input.clear()
        self.controller.clear_structured_filter()

    def clear_custom_sort(self):
        self.custom_sort_input.setCurrentText("")
        self.controller.clear_custom_sort()
        self.sort_order_selector.setCurrentText("Asc")
