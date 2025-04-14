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
)
from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtGui import QPalette, QColor, QKeySequence
from logger import setup_logger
from PyQt5.QtWidgets import QTableView
from table_model import DataTableModel
from PyQt5.QtCore import QTimer
from utils import get_save_time_label_text

logger = setup_logger("gui")


class MainWindow(QMainWindow):
    """
    Main GUI for user interaction with saved data and IU configurations
    (profiles) & data configurations.


    Attributes:
        data_manager (Data_Manager): controls how data is saved and loaded.
    """

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

        # Todo: keep these from being order dependent
        self.layout = QVBoxLayout()
        self.load_data()

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
        self.search_box.textChanged.connect(self.search_data)

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
        self.layout.addWidget(self.search_box)
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

        # Create the model
        self.model = DataTableModel(
            raw_data, headers, data_manager=self.data_manager
        )
        self.table_view = QTableView()
        self.table_view.setModel(self.model)
        self.table_view.resizeColumnsToContents()
        self.layout.addWidget(self.table_view)

    def switch_profile(self):
        """
        Handles switching user profiles.
        """
        self.current_profile = self.profile_selector.currentText()
        self.config = load_config(self.current_profile)
        if self.theme_selector:
            self.theme_selector.setCurrentText(
                "Dark" if self.config.get("dark_mode", False) else "Light"
            )
        self.apply_theme()
        print(f"Switched to profile: {self.current_profile}")

    def update_theme(self):
        """
        Applies the selected theme and saves it to the user profile.
        """
        self.config["dark_mode"] = self.theme_selector.currentText() == "Dark"
        save_config(self.config, self.current_profile)
        self.apply_theme()
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

    def search_data(self):
        query = self.search_box.text()
        print("Searching for: ", query)

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
