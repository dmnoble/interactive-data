# main.py
import sys
from PyQt5.QtWidgets import QApplication, QMessageBox
from gui import MainWindow
from data_manager import DataManager
from logger import setup_logger
from version import __version__

"""
@todo
    -   Details window for data
    -   Data interactions: open link, open file, group data, etc.
    -   Allow simple text search to be combined with structured
        filter (Filter: Alice or age == 32)
    -   Configuration for data input page
@bug
    -   Putting in an incorrect sort key, sort results to show
        None, then Apply Custom Sort doesn't work until the Clear
        button is selected
    -   When putting in an incorrect or incomplete equation
        for filtering, the table goes blank and several
        repeats of this error comes up
            SyntaxError: invalid syntax (<unknown>, line 1)
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
