# gui.py
import logging

from PyQt5.QtWidgets import (
    QComboBox,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QHBoxLayout,
    QTableView,
)

from version import __version__

logger = logging.getLogger(__name__)


class BuildGui(QMainWindow):
    """
    Main GUI for user interaction with saved data and IU configurations
    (profiles) & data configurations.
    """

    def __init__(self, table_view: QTableView) -> None:
        super().__init__()
        self.setWindowTitle("Interactive Data Workspace")

        self._init_ui()
        self._apply_ui(table_view)
        self.set_filter_defaults()
        self.set_sort_defaults()

        # Connect custom expression help button
        self.custom_expr_help_button.clicked.connect(
            self.show_filter_expr_help
        )

        # Connect custom sort help button
        self.custom_sort_help_button.clicked.connect(self.show_sort_expr_help)

    def _init_ui(self) -> None:
        # Main widget
        self.central_widget = QWidget()

        # Profile
        self.profile_label = QLabel("Select Profile:")
        self.profile_selector = QComboBox()
        self.add_profile_button = QPushButton("Add Profile")

        # Theme
        self.theme_label = QLabel("Select Theme:")
        self.theme_selector = QComboBox()
        self.theme_selector.addItems(["Light", "Dark"])

        # Undo/Redo
        self.undo_button = QPushButton("Undo (Ctrl+Z)")
        self.undo_history_combo: QComboBox = QComboBox()
        self.undo_history_combo.setPlaceholderText("Undo History")
        self.redo_button = QPushButton("Redo (Ctrl+Y)")
        self.redo_history_combo: QComboBox = QComboBox()
        self.redo_history_combo.setPlaceholderText("Redo History")

        # Views
        self.view_selector: QComboBox = QComboBox()
        self.view_selector.setPlaceholderText("Load Saved View")
        self.save_view_button = QPushButton("Save Current View")
        self.set_default_button = QPushButton("Set as Default View")

        # Filtering
        self.field_selector: QComboBox = QComboBox()
        self.field_selector.setPlaceholderText("Field")
        self.custom_filter_input: QLineEdit = QLineEdit()
        self.operator_selector: QComboBox = QComboBox()
        self.value_input: QLineEdit = QLineEdit()
        self.case_checkbox: QCheckBox = QCheckBox("Case Sensitive")
        self.operator_selector.addItems(["==", "!=", ">", "<", ">=", "<="])
        self.value_input.setPlaceholderText("Value")
        self.structured_ok_button = QPushButton("OK")
        self.clear_filter_button = QPushButton("Clear")
        self.custom_expr_help_button = QPushButton("?")
        self.custom_expr_label = QLabel("Filter: ")

        # Sorting
        self.custom_sort_input: QComboBox = QComboBox()
        self.custom_sort_input.setEditable(True)
        self.custom_sort_input.setInsertPolicy(QComboBox.InsertAtTop)
        self.sort_order_selector: QComboBox = QComboBox()
        self.sort_order_selector.addItems(["Asc", "Desc"])
        self.sort_label = QLabel("Sort: ")
        self.clear_sort_button = QPushButton("Clear")
        self.apply_sort_button = QPushButton("Apply Custom Sort")
        self.custom_sort_help_button = QPushButton("?")

        # App information
        self.save_label = QLabel("Last saved: just now")
        self.version_label = QLabel(f"v{__version__} running")

    def _apply_ui(self, table_view: QTableView) -> None:
        # Main widget
        self.main_layout = QVBoxLayout()
        self.central_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.central_widget)

        # Profile
        profile_layout = QHBoxLayout()
        profile_layout.addWidget(self.add_profile_button)
        profile_layout.addWidget(self.profile_label)
        profile_layout.addWidget(self.profile_selector)
        self.main_layout.addLayout(profile_layout)

        # Data table view
        self.main_layout.addWidget(table_view)

        # Theme
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(self.theme_label)
        theme_layout.addWidget(self.theme_selector)
        self.main_layout.addLayout(theme_layout)

        # Undo/Redo
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.undo_button)
        button_layout.addWidget(self.redo_button)
        self.main_layout.addLayout(button_layout)
        combo_layout = QHBoxLayout()
        combo_layout.addWidget(self.undo_history_combo)
        combo_layout.addWidget(self.redo_history_combo)
        self.main_layout.addLayout(combo_layout)

        # Views
        view_layout = QHBoxLayout()
        view_layout.addWidget(self.save_view_button)
        view_layout.addWidget(self.view_selector)
        view_layout.addWidget(self.set_default_button)
        self.main_layout.addLayout(view_layout)

        # Filtering
        search_layout = QHBoxLayout()
        search_layout.addWidget(self.clear_filter_button)
        search_layout.addWidget(self.custom_expr_label)
        search_layout.addWidget(self.custom_filter_input)
        search_layout.addWidget(self.case_checkbox)
        search_layout.addWidget(self.custom_expr_help_button)
        self.main_layout.addLayout(search_layout)
        structured_layout = QHBoxLayout()
        structured_layout.addWidget(self.field_selector)
        structured_layout.addWidget(self.operator_selector)
        structured_layout.addWidget(self.value_input)
        structured_layout.addWidget(self.structured_ok_button)
        self.main_layout.addLayout(structured_layout)

        # Sorting
        sort_layout = QHBoxLayout()
        sort_layout.addWidget(self.clear_sort_button)
        sort_layout.addWidget(self.sort_label)
        sort_layout.addWidget(self.custom_sort_input)
        sort_layout.addWidget(self.sort_order_selector)
        sort_layout.addWidget(self.apply_sort_button)
        sort_layout.addWidget(self.custom_sort_help_button)
        self.main_layout.addLayout(sort_layout)

        # App information
        self.main_layout.addWidget(self.save_label)
        footer_layout = QHBoxLayout()
        self.version_label.setStyleSheet("color: gray; font-size: 10px;")
        footer_layout.addWidget(self.version_label)
        footer_layout.addStretch()  # Push label to the left or right
        self.main_layout.addLayout(footer_layout)

    def update_filter_operators(self, sample_value) -> None:
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

    def on_apply_structured_filter(self) -> None:
        field = self.field_selector.currentText()
        operator = self.operator_selector.currentText()
        clean_value = self.value_input.text()

        if not field or not operator:
            return

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
                expr = f"{value} in {field}"
            case "not":
                expr = f"{value} not in {field}"
            case "matches":
                expr = f"{value} in {field}"
            case "startswith":
                expr = f"{field}.startswith({value})"
            case "endswith":
                expr = f"{field}.endswith({value})"
            case _:
                expr = f"{field} {operator} {value}"

        # ➡️ Append to existing custom expression if present
        current_expr = self.custom_filter_input.text().strip()

        if current_expr:
            combined_expr = f"{current_expr} and {expr}"
        else:
            combined_expr = expr

        self.custom_filter_input.setText(combined_expr)

        # ✅ CLEAR structured fields after inserting
        self.field_selector.setCurrentIndex(-1)
        self.operator_selector.clear()
        self.value_input.clear()

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

    def get_current_view_name(self) -> str:
        return self.view_selector.currentText()

    def set_view_selector(self, view_name: str) -> None:
        index = self.view_selector.findText(view_name)
        if index != -1:
            self.view_selector.setCurrentIndex(index)

    def set_filter_defaults(self) -> None:
        self.custom_filter_input.clear()
        self.custom_filter_input.setPlaceholderText(
            "Custom Filter Expression (e.g. status == 'active')"
        )

    def set_sort_defaults(self) -> None:
        self.custom_sort_input.setCurrentText("")
        line_edit = self.custom_sort_input.lineEdit()
        placeholder = "Enter Custom Sort Key (e.g. len(name) + priority)"
        line_edit.setPlaceholderText(placeholder)
        self.sort_order_selector.setCurrentText("Asc")

    def refresh_view_selector(
        self, all_views: list[str], default_name: str | None
    ) -> None:
        self.view_selector.clear()
        for name in all_views:
            label = f"{name} (default)" if name == default_name else name
            self.view_selector.addItem(label)

        if not default_name:
            return

        # Ensure the current selection stays highlighted
        self.set_view_selector(f"{default_name} (default)")

    # def update_profile_list(self, profiles: list[str]) -> None:
    #     """
    #     Refresh the profile list from existing config files.
    #     """
    #     self.profile_selector.clear()
    #     self.profile_selector.addItems(profiles)

    def update_undo_redo_history(
        self, undo_stack: list, redo_stack: list
    ) -> None:
        self.undo_history_combo.clear()
        self.redo_history_combo.clear()
        for action in reversed(undo_stack):
            self.undo_history_combo.addItem(action.description())
        for action in reversed(redo_stack):
            self.redo_history_combo.addItem(action.description())

    # def closeEvent(self, event) -> None:
    #     self.controller.auto_backup_if_needed()
    #     self.controller.check_dirty_and_save()
    #     event.accept()
