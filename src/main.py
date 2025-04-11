# main.py
import sys
from PyQt5.QtWidgets import QApplication, QMessageBox
from gui import MainWindow
from data_manager import DataManager
from logger import setup_logger
from version import __version__

"""
@todo
    -   Visuals for data (table, details window, etc)
    -   Handle situation where there is no previous data
    -   Figure out how to implement the theme if there is no previous
        profile
"""

logger = setup_logger("main")


def log_uncaught_exceptions(exctype, value, traceback):
    logger.error("Uncaught exception", exc_info=(exctype, value, traceback))
    QMessageBox.critical(None, "Unexpected Error", f"{value}")
    sys.__excepthook__(exctype, value, traceback)


sys.excepthook = log_uncaught_exceptions

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Force the style to be the same on all OSs:
    app.setStyle("Fusion")

    data_manager = DataManager()
    main_window = MainWindow(data_manager, __version__)
    main_window.show()
    sys.exit(app.exec_())
