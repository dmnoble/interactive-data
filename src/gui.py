# gui.py
import sys
from config import load_config, save_config, get_profiles, DEFAULT_CONFIG
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
    QTableView,
    QCheckBox,
    QHeaderView,
    QApplication,
    QMessageBox,
)
from PyQt5.QtCore import Qt, QDateTime, QTimer
from PyQt5.QtGui import QPalette, QColor, QKeySequence
from logger import setup_logger
from filter_proxy import TableFilterProxyModel
from table_model import DataTableModel
from utils import get_save_time_label_text
from rich_text_delegate import RichTextDelegate
from view_config import (
    save_view_config,
    get_all_view_names,
    get_default_view_name,
    set_default_view,
)

logger = setup_logger("gui")


class MainWindow(QMainWindow):
    """
    Main GUI for user interaction with saved data and IU configurations
    (profiles) & data configurations.


    Attributes:
        data_manager (Data_Manager): controls how data is saved and loaded.
    """

    proxy_model = TableFilterProxyModel()
    config = None
    view_selector = None
    field_selector = None
    model = None

    def __init__(self, data_manager, version):
        """
        Initiates data manager for user to interact with data.

        Handles fresh start situation (no previously existing profiles)

        Supplies user capabilities:
            -   UI configuration (profiles), including selecting, loading, and
            saving
            -   Data handling such as displaying, filtering, sorting
        """
        super().__init__()
        self.data_manager = data_manager
        self.setWindowTitle("Data Manager App")

        # Auto-Save Logic
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.check_dirty_and_save)
        self.auto_save_timer.start(5 * 60 * 1000)  # Every 5 minutes

        # GUI label for time since last save
        self.last_save_time = QDateTime.currentDateTime()
        self.save_label = QLabel("Last saved: just now")
        self.save_timer = QTimer()
        self.save_timer.timeout.connect(self.update_save_label)
        self.save_timer.start(60 * 1000)  # every minute

        # Timer for the hourly backup
        self.backup_timer = QTimer()
        self.backup_timer.timeout.connect(self.auto_backup_if_needed)
        self.backup_timer.start(60 * 60 * 1000)  # every hour in ms

        # Profile selection dropdown
        self.profile_label = QLabel("Select Profile:")
        profile_layout = QHBoxLayout()
        self.profile_selector = QComboBox()
        self.update_profile_list()
        self.add_profile_button = QPushButton("Add Profile")
        self.add_profile_button.clicked.connect(self.create_new_profile)
        profile_layout.addWidget(self.profile_selector)
        profile_layout.addWidget(self.add_profile_button)

        # Check if profiles exist, if not prompt user for a new one
        if not self.profile_selector.count():
            self.create_new_profile()
        self.current_profile = self.profile_selector.currentText()

        # Set function call in response to changing profile selection
        self.profile_selector.currentIndexChanged.connect(self.switch_profile)

        # Load user's settings
        self.config = load_config(self.current_profile)

        self.layout = QVBoxLayout()

        # Theme Selector
        self.theme_label = QLabel("Select Theme:")
        self.theme_selector = QComboBox()
        self.theme_selector.addItems(["Light", "Dark"])
        self.theme_selector.setCurrentText(
            "Dark" if self.config.get("dark_mode", False) else "Light"
        )
        self.theme_selector.currentIndexChanged.connect(self.update_theme)

        # Data handling
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search data...")
        self.case_checkbox = QCheckBox("Case Sensitive")
        self.case_checkbox.setChecked(False)
        self.case_checkbox.stateChanged.connect(
            lambda state: self.proxy_model.set_case_sensitive(
                state == Qt.Checked
            )
        )

        # Save View Button
        self.save_view_button = QPushButton("Save Current View")
        self.save_view_button.clicked.connect(self.save_current_view)

        # View Loader Dropdown
        self.view_selector = QComboBox()
        self.view_selector.setPlaceholderText("Load Saved View")
        self.view_selector.activated[str].connect(self.load_selected_view)
        # Populate view names at startup
        self.refresh_view_selector()

        # Default view button
        self.set_default_button = QPushButton("Set as Default View")
        self.set_default_button.clicked.connect(self.set_default_view)

        # Filter
        self.field_selector = QComboBox()
        self.field_selector.setPlaceholderText("Field")
        self.field_selector.currentTextChanged.connect(
            self.update_filter_operators
        )
        self.operator_selector = QComboBox()
        self.operator_selector.addItems(["==", "!=", ">", "<", ">=", "<="])
        self.operator_selector.currentTextChanged.connect(
            self.update_structured_filter
        )
        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("Value")
        self.value_input.textChanged.connect(self.update_structured_filter)

        self.custom_expr_input = QLineEdit()
        self.custom_expr_input.setPlaceholderText(
            "Custom Filter Expression (e.g. status == 'active')"
        )
        self.custom_expr_input.textChanged.connect(
            self.update_custom_filter_expr
        )

        self.custom_expr_input = QLineEdit()
        self.custom_expr_input.setPlaceholderText(
            "Custom Filter Expression (e.g. status == 'active')"
        )
        self.custom_expr_input.textChanged.connect(
            self.update_custom_filter_expr
        )

        self.custom_expr_help_button = QPushButton("?")
        self.custom_expr_help_button.setFixedWidth(25)
        self.custom_expr_help_button.clicked.connect(
            self.show_filter_expr_help
        )

        # Custom sort
        self.custom_sort_input = QComboBox()
        self.custom_sort_input.setEditable(True)
        self.custom_sort_input.setInsertPolicy(QComboBox.InsertAtTop)
        # Insert a fake placeholder item
        placeholder = "Enter Custom Sort Key (e.g. len(name) + priority)"
        line_edit = self.custom_sort_input.lineEdit()
        line_edit.setPlaceholderText(placeholder)

        self.apply_sort_button = QPushButton("Apply Custom Sort")
        self.apply_sort_button.clicked.connect(self.apply_custom_sort)

        self.sort_order_selector = QComboBox()
        self.sort_order_selector.addItems(["Ascending", "Descending"])

        self.custom_sort_help_button = QPushButton("?")
        self.custom_sort_help_button.setFixedWidth(25)
        self.custom_sort_help_button.clicked.connect(self.show_sort_expr_help)

        # Todo: keep these from being order dependent
        self.load_data()

        # Search
        self.table_view.setModel(self.proxy_model)
        self.table_view.setTextElideMode(Qt.ElideNone)  # allow wrapping
        self.search_box.textChanged.connect(self.proxy_model.set_search_text)
        # Add to layout
        self.button = QPushButton("Load Data")
        self.button.clicked.connect(self.load_data)

        # Undo Redo
        # Add buttons:
        self.undo_button = QPushButton("Undo (Ctrl+Z)")
        self.redo_button = QPushButton("Redo (Ctrl+Y)")
        self.undo_button.clicked.connect(self.model.undo)
        self.redo_button.clicked.connect(self.model.redo)

        # Add to layout:
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.undo_button)
        button_layout.addWidget(self.redo_button)

        # Add shortcuts:
        undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self)
        redo_shortcut = QShortcut(QKeySequence("Ctrl+Y"), self)
        undo_shortcut.activated.connect(self.model.undo)
        redo_shortcut.activated.connect(self.model.redo)

        # Undo/Redo history pulldown
        self.undo_history_combo = QComboBox()
        self.redo_history_combo = QComboBox()
        self.undo_history_combo.setPlaceholderText("Undo History")
        self.redo_history_combo.setPlaceholderText("Redo History")

        # Add to layout (next to undo/redo buttons):
        combo_layout = QHBoxLayout()
        combo_layout.addWidget(self.undo_history_combo)
        combo_layout.addWidget(self.redo_history_combo)

        # Connect to model update:
        self.model.stack_changed.connect(self.update_undo_redo_history)

        # Apply the UI
        self.layout.addLayout(button_layout)
        self.layout.addLayout(combo_layout)
        self.layout.addWidget(self.profile_label)
        self.layout.addLayout(profile_layout)
        self.layout.addWidget(self.theme_label)
        self.layout.addWidget(self.theme_selector)
        view_layout = QHBoxLayout()
        view_layout.addWidget(self.save_view_button)
        view_layout.addWidget(self.view_selector)
        view_layout.addWidget(self.set_default_button)
        self.layout.addLayout(view_layout)
        self.layout.addWidget(self.search_box)
        search_layout = QHBoxLayout()
        search_layout.addWidget(self.custom_expr_input)
        search_layout.addWidget(self.case_checkbox)
        search_layout.addWidget(self.custom_expr_help_button)
        self.layout.addLayout(search_layout)
        structured_layout = QHBoxLayout()
        structured_layout.addWidget(self.field_selector)
        structured_layout.addWidget(self.operator_selector)
        structured_layout.addWidget(self.value_input)
        self.layout.addLayout(structured_layout)
        self.layout.addWidget(self.custom_sort_input)
        sort_controls_layout = QHBoxLayout()
        sort_controls_layout.addWidget(self.sort_order_selector)
        sort_controls_layout.addWidget(self.apply_sort_button)
        sort_controls_layout.addWidget(self.custom_sort_help_button)
        self.layout.addLayout(sort_controls_layout)
        self.layout.addWidget(self.button)
        self.layout.addWidget(self.save_label)

        # Footer layout for version info
        footer_layout = QHBoxLayout()
        self.version_label = QLabel(f"v{version} running")
        self.version_label.setStyleSheet("color: gray; font-size: 10px;")
        footer_layout.addWidget(self.version_label)
        footer_layout.addStretch()  # Push label to the left or right

        # Add to main layout
        self.layout.addLayout(footer_layout)

        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

        # Apply theme after loading profile
        self.apply_theme()

    def check_dirty_and_save(self):
        if self.model and self.model.is_dirty():
            try:
                data = self.model.get_current_data_as_dicts()
                self.data_manager.save_data(data)
                self.last_save_time = QDateTime.currentDateTime()
                self.model.mark_clean()

                self.unsaved_action_stack.clear()
                if self.undo_log_path.exists():
                    self.undo_log_path.unlink()

                print("Auto-save complete.")
            except Exception as e:
                print("Auto-save failed:", e)

    def update_save_label(self):
        self.save_label.setText(get_save_time_label_text(self.last_save_time))

    def auto_backup_if_needed(self):
        """
        Auto-Backup every hour and on close
        """
        if self.model and self.model.is_backup_dirty():
            try:
                data = self.model.get_current_data_as_dicts()
                self.data_manager.save_backup(data)
                self.model.mark_backup_clean()
            except Exception as e:
                print("Auto-backup failed:", e)

    def load_data(self):
        """
        Response to user selecting to load data

        Returns:
            dict: The data loaded from  profile data file.
        """
        # Load real data from DataManager
        raw_data = self.data_manager.load_data()

        # Dynamically get headers from first item (or fallback)
        headers = list(raw_data[0].keys()) if raw_data else []
        self.field_selector.clear()
        self.field_selector.addItems(headers)
        self.update_filter_operators()  # Run after headers added

        # Create the model
        self.model = DataTableModel(
            raw_data,
            headers,
            data_manager=self.data_manager,
            proxy_model=self.proxy_model,
            dark_mode=self.config.get("dark_mode", False),
        )
        self.proxy_model.setSourceModel(self.model)
        self.table_view = QTableView()
        self.table_view.setModel(self.model)
        # Render HTML in cells — including the fancy
        # substring <span style=...> highlights from search.
        self.table_view.setItemDelegate(RichTextDelegate())
        # Start compact: auto-size to content initially
        self.table_view.horizontalHeader().setStretchLastSection(False)
        self.table_view.horizontalHeader().setSectionResizeMode(
            QHeaderView.Interactive
        )
        # Give Qt a moment to measure based on the new delegate rendering
        QTimer.singleShot(0, self.table_view.resizeColumnsToContents)
        self.table_view.setWordWrap(False)
        self.table_view.setTextElideMode(Qt.ElideRight)
        self.table_view.setSortingEnabled(True)
        self.layout.addWidget(self.table_view)

        self.refresh_view_selector()  # make sure the dropdown is populated

        default_view = get_default_view_name()
        if default_view:
            self.load_selected_view(default_view)
            index = self.view_selector.findText(f"{default_view} (default)")
            if index != -1:
                self.view_selector.setCurrentIndex(index)

    def switch_profile(self):
        """
        Handles switching user profiles.
        """
        if self.current_profile == self.profile_selector.currentText():
            return
        self.current_profile = self.profile_selector.currentText()
        self.config = load_config(self.current_profile)
        if self.theme_selector:
            self.theme_selector.setCurrentText(
                "Dark" if self.config.get("dark_mode", False) else "Light"
            )
        self.apply_theme()
        if self.model:
            try:
                data = self.model.get_current_data_as_dicts()
                self.data_manager.save_data(data)
                if self.model.undo_stack:
                    self.model.undo_stack.clear()
                if self.model.redo_stack:
                    self.model.redo_stack.clear()
                if self.model.unsaved_action_stack:
                    self.model.unsaved_action_stack.clear()
                if self.model.undo_log_path.exists():
                    self.model.undo_log_path.unlink()
                print("Auto-save complete before profile switch.")
            except Exception as e:
                print("Auto-save before profile switch failed:", e)
        # Clear history dropdowns
        self.undo_history_combo.clear()
        self.redo_history_combo.clear()

        print(f"Switched to profile: {self.current_profile}")

    def update_theme(self):
        """
        Applies the selected theme and saves it to the user profile.
        """
        self.config["dark_mode"] = self.theme_selector.currentText() == "Dark"
        save_config(self.config, self.current_profile)
        self.apply_theme()
        if self.model:
            self.model.set_dark_mode(self.config["dark_mode"])
        print(
            f"Theme updated for {self.current_profile}"
            + f" to {self.theme_selector.currentText()}"
        )

    def apply_theme(self):
        """
        Applies the current user's theme settings.
        """
        if self.config.get("dark_mode", False):
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
            save_config(
                DEFAULT_CONFIG, new_profile
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
        self.profile_selector.addItems(get_profiles())

    def update_undo_redo_history(self):
        self.undo_history_combo.clear()
        self.redo_history_combo.clear()
        for action in reversed(self.model.undo_stack):
            self.undo_history_combo.addItem(action.description())
        for action in reversed(self.model.redo_stack):
            self.redo_history_combo.addItem(action.description())

    def closeEvent(self, event):
        self.auto_backup_if_needed()
        self.check_dirty_and_save()
        event.accept()

    def save_current_view(self):
        dialog = QInputDialog(self)
        dialog.setWindowTitle("Save View")
        dialog.setLabelText("Enter view name:")

        if self.config.get("dark_mode", False):
            dark_palette = QPalette()
            dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.WindowText, Qt.white)
            dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
            dark_palette.setColor(QPalette.Text, Qt.white)
            dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ButtonText, Qt.white)
            dialog.setPalette(dark_palette)
        else:
            dialog.setPalette(
                QApplication.palette()
            )  # system default for light

        ok = dialog.exec_()
        name = dialog.textValue()

        if ok and name:
            config = {
                "name": name,
                "search_text": self.search_box.text(),
                "case_sensitive": self.case_checkbox.isChecked(),
                "sort_column": (
                    self.table_view.horizontalHeader().sortIndicatorSection()
                ),
                "ascending": (
                    self.table_view.horizontalHeader().sortIndicatorOrder()
                    == Qt.AscendingOrder
                ),
                "filter": {
                    "field": self.field_selector.currentText(),
                    "operator": self.operator_selector.currentText(),
                    "value": self.value_input.text(),
                },
                "custom_filter": self.custom_expr_input.text(),
                "custom_sort_key": self.custom_sort_input.currentText(),
            }

            save_view_config(name, config)
            self.refresh_view_selector()
            index = self.view_selector.findText(name)
            if index != -1:
                self.view_selector.setCurrentIndex(index)

    def load_selected_view(self, name):
        from view_config import get_view_config

        cleaned_name = name.replace(" (default)", "")
        config = get_view_config(cleaned_name)

        config = get_view_config(cleaned_name)
        if not config:
            return
        self.search_box.setText(config.get("search_text", ""))
        self.proxy_model.set_search_text(self.search_box.text())
        self.case_checkbox.setChecked(config.get("case_sensitive", False))
        self.table_view.sortByColumn(
            config.get("sort_column", 0),
            (
                Qt.AscendingOrder
                if config.get("ascending", True)
                else Qt.DescendingOrder
            ),
        )

        filter_config = config.get("filter", {})
        self.field_selector.setCurrentText(filter_config.get("field", ""))
        self.update_filter_operators()
        self.operator_selector.setCurrentText(
            filter_config.get("operator", "==")
        )
        self.value_input.setText(filter_config.get("value", ""))
        self.custom_expr_input.setText(config.get("custom_filter", ""))

        self.custom_sort_input.setCurrentText(
            config.get("custom_sort_key", "")
        )

    def refresh_view_selector(self):
        from view_config import get_default_view_name

        all_views = get_all_view_names()
        default_name = get_default_view_name()

        self.view_selector.clear()
        for name in all_views:
            label = f"{name} (default)" if name == default_name else name
            self.view_selector.addItem(label)

    def update_structured_filter(self):
        field = self.field_selector.currentText()
        op = self.operator_selector.currentText()
        value = self.value_input.text()
        self.proxy_model.set_structured_filter(field, op, value)

    def update_custom_filter_expr(self):
        expr = self.custom_expr_input.text()
        self.proxy_model.set_custom_filter_expression(expr)

    def apply_custom_sort(self):
        expr = self.custom_sort_input.currentText().strip()

        # Skip placeholder
        if not expr or expr.startswith("Enter Custom Sort"):
            return

        # This sets sort column to 0 and triggers ascending sort
        # Which activates proxy's lessThan()ef apply_custom_sort(self):
        if self.custom_sort_input.findText(expr) == -1:
            self.custom_sort_input.insertItem(0, expr)
        self.proxy_model.set_custom_sort_key(expr)
        sort_order = (
            Qt.AscendingOrder
            if self.sort_order_selector.currentText() == "Ascending"
            else Qt.DescendingOrder
        )
        self.table_view.sortByColumn(0, sort_order)

    def set_default_view(self):
        name = self.view_selector.currentText().replace(" (default)", "")
        if name:
            set_default_view(name)
            self.refresh_view_selector()
            # Ensure the current selection stays highlighted
            index = self.view_selector.findText(f"{name} (default)")
            if index != -1:
                self.view_selector.setCurrentIndex(index)

    def update_filter_operators(self):
        if not self.model:
            return

        field = self.field_selector.currentText()

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
            "Field names (columns) are available as variables.\n"
            "For example, use 'priority', 'status', 'tags', 'name', etc."
        )
        msg.setIcon(QMessageBox.NoIcon)  # <- No chime!
        msg.exec_()

    def show_sort_expr_help(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Custom Sort Key Help")
        msg.setText(
            "Examples:\n"
            "  len(name)\n"
            "  priority * 2 + score\n"
            "  int(status == 'active')  # Sort true before false\n\n"
            "You can use:\n"
            "  - len(x)\n"
            "  - str(), int(), float()\n"
            "  - min(), max(), round()\n\n"
            "Field names (columns) are available as variables."
        )
        msg.setIcon(QMessageBox.NoIcon)  # <- No chime!
        msg.exec_()
