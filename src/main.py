# main.py

"""
  Startup entry point for Interactive Data Workspace.

# TODO:
- Details window for data
- Data interactions: open link, open file, group data, etc.
- Allow simple text search to be combined with structured filter
  (e.g. Filter: Alice or age == 32)
- Configuration for data input page

# FIXME:
- Sample data RewatchScheduler Alice view doesn't work
- View selector doesn't update when view is changed
- Sort expression "len(description)" sometimes crashes
- Incorrect sort key causes None values; Apply Sort doesn't work
  until Clear is pressed
- Invalid filter equations cause blank tables and error messages
  (e.g., SyntaxError: invalid syntax (<unknown>, line 1))
"""

import sys
from PyQt5.QtWidgets import QApplication, QMessageBox
from gui import BuildGui
from gui_presenter import GuiPresenter
from workspace_controller import WorkspaceController
from logger import setup_logger


logger = setup_logger("main")


def log_uncaught_exceptions(exctype, value, traceback):
    """Global exception handler that logs and shows a user message box."""
    logger.error("Uncaught exception", exc_info=(exctype, value, traceback))
    QMessageBox.critical(None, "Unexpected Error", f"{value}")
    sys.__excepthook__(exctype, value, traceback)


sys.excepthook = log_uncaught_exceptions

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Ensure consistent style across OSes

    main_window = BuildGui()
    controller = WorkspaceController()
    presenter = GuiPresenter(controller, main_window)
    main_window.show()
    sys.exit(app.exec_())
