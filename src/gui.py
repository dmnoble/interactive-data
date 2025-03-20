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
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor


class MainWindow(QMainWindow):
    """
    Main GUI for user interaction with saved data and IU configurations
    (profiles) & data configurations.


    Attributes:
        data_manager (Data_Manager): controls how data is saved and loaded.
    """

    def __init__(self, data_manager):
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

        self.layout = QVBoxLayout()

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
            self.update_profile_list()
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

        self.button = QPushButton("Load Data")
        self.button.clicked.connect(self.load_data)

        # Apply the UI
        self.layout.addWidget(self.profile_label)
        self.layout.addLayout(profile_layout)
        self.layout.addWidget(self.theme_label)
        self.layout.addWidget(self.theme_selector)
        self.layout.addWidget(self.search_box)
        self.layout.addWidget(self.button)

        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

        # Apply theme after loading profile
        self.apply_theme()

    def load_data(self):
        """
        Response to user selecting to load data

        Returns:
            dict: The data loaded from  profile data file.
        """
        data = self.data_manager.load_data()
        print(f"Data Loaded for {self.current_profile}:", data)

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
            self.profile_selector.setCurrentText(new_profile)
        else:
            sys.exit()

    def update_profile_list(self):
        """
        Refresh the profile list from existing config files.
        """
        self.profile_selector.clear()
        self.profile_selector.addItems(get_profiles())
