# gui.py
from PyQt5.QtWidgets import (
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QComboBox,
    QLabel,
    QLineEdit,
)
from config import load_config, save_config
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor


class MainWindow(QMainWindow):
    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self.setWindowTitle("Data Manager App")
        self.config = load_config()

        self.layout = QVBoxLayout()

        self.theme_label = QLabel("Select Theme:")
        self.theme_selector = QComboBox()
        self.theme_selector.addItems(["Light", "Dark"])
        self.apply_saved_theme()
        self.theme_selector.currentIndexChanged.connect(self.update_theme)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search data...")
        self.search_box.textChanged.connect(self.search_data)

        self.button = QPushButton("Load Data")
        self.button.clicked.connect(self.load_data)

        self.layout.addWidget(self.theme_label)
        self.layout.addWidget(self.theme_selector)
        self.layout.addWidget(self.search_box)
        self.layout.addWidget(self.button)

        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

    def apply_saved_theme(self):
        self.theme_selector.setCurrentText(
            "Dark" if self.config.get("dark_mode", False) else "Light"
        )
        self.update_theme()

    def load_data(self):
        data = self.data_manager.load_data()
        print("Data Loaded:", data)

    def update_theme(self):
        if self.theme_selector.currentText() == "Dark":
            self.config["dark_mode"] = True
            # Now use a palette to switch to dark colors:
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
            # QToolTip::setPalette(palette)
        else:
            self.config["dark_mode"] = False
            self.setPalette(QPalette())
            pass

        save_config(self.config)
        print("Theme updated to:", self.theme_selector.currentText())

    def search_data(self):
        query = self.search_box.text()
        print("Searching for:", query)
