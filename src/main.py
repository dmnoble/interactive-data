# main.py
import sys
from PyQt5.QtWidgets import QApplication
from gui import MainWindow
from data_manager import DataManager

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Force the style to be the same on all OSs:
    app.setStyle("Fusion")

    data_manager = DataManager()
    main_window = MainWindow(data_manager)
    main_window.show()
    sys.exit(app.exec_())
