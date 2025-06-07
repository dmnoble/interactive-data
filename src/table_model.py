import json
from pathlib import Path
from typing import Optional
from undo_redo import Action
from PyQt5.QtWidgets import QMessageBox
import os

# import copy
import logging


from typing import Any
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, pyqtSignal

logger = logging.getLogger(__name__)


class DataTableModel(QAbstractTableModel):
    """
    A Qt-compatible table model for displaying and editing structured user
    data.

    This model supports:
    - Displaying a list of dictionaries as rows in a QTableView
    - Editable cells with change detection
    - Auto-saving through a connected DataManager (on real changes only)
    - Tracking of 'dirty' state for periodic auto-saves
    - Tracking of 'backup-dirty' state for controlled backup generation
    - Optional extraction of headers from the input data

    Designed for seamless integration into an interactive data viewing app,
    this model prioritizes reliability, real-time feedback, and user
    transparency.
    """

    RAW_VALUE_ROLE = Qt.UserRole + 1
    stack_changed = pyqtSignal()

    def __init__(
        self,
        data: list[dict],
        headers: Optional[list[str]] = None,
        data_manager: Optional[Any] = None,
        proxy_model: Optional[Any] = None,
        dark_mode: bool = False,
    ):
        super().__init__()

        self._raw_data = data or []
        self._data_manager = data_manager
        self._proxy_model = proxy_model
        self._dark_mode = dark_mode

        self.undo_stack: list[Action] = []
        self.redo_stack: list[Action] = []
        self.unsaved_action_stack: list[Action] = []
        self._dirty: bool = False
        self._backup_dirty: bool = False

        self.undo_log_path: Path = Path(".undo_log.json")
        self.stack_changed.connect(self.write_recovery_log_to_file)
        if headers:
            self._headers = headers.copy()  # real headers from the loaded data
        else:
            self._headers = (
                list(self._raw_data[0].keys()) if self._raw_data else []
            )

        if self.undo_log_path.exists():
            test_mode = os.environ.get("IDW_TEST_MODE") == "1"
            if test_mode or self.prompt_user_for_recovery():
                self.load_undo_stack_from_file()
                self.replay_undo_stack()
            else:
                self.undo_log_path.unlink()

        self._data = [
            [item.get(header, "") for header in self._headers]
            for item in self._raw_data
        ]

        if "sort key" not in self._headers:
            # 🛠 Inject sort result virtual header
            self._headers.append("sort key")

        # 🛠 Inject blank sort result field into each data row
        for row in self._data:
            row.append("")

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._data)

    def columnCount(self, parent=QModelIndex()) -> int:
        if not hasattr(self, "_headers") or self._headers is None:
            return 0
        return len(self._headers)

    def data(self, index: QModelIndex, role=Qt.DisplayRole) -> Any:
        if not index.isValid():
            return None

        row = index.row()
        column = index.column()

        # If this is a regular column

        value = self._data[row][column]

        if role == Qt.DisplayRole:
            display = str(value)
            if self._proxy_model:
                search = self._proxy_model.search_text
                case_sensitive = getattr(
                    self._proxy_model, "case_sensitive", False
                )
                if search:
                    text_to_search = (
                        display if case_sensitive else display.lower()
                    )
                    search_key = search if case_sensitive else search.lower()
                    if search_key in text_to_search:
                        start = text_to_search.index(search_key)
                        end = start + len(search_key)
                        # soft blue or yellow
                        bg_color = "#505b76" if self._dark_mode else "#ffff00"
                        text_color = "white" if self._dark_mode else "black"

                        # Highlight only the match but apply text color to
                        # entire span
                        highlighted = (
                            f'<span style="color: {text_color}">'
                            + display[:start]
                            + f'<span style="background-color: {bg_color}">'
                            + f"{display[start:end]}</span>"
                            + display[end:]
                            + "</span>"
                        )
                        return highlighted
            # Default: wrap full text to apply text color even with no match
            text_color = "white" if self._dark_mode else "black"
            return f'<span style="color: {text_color}">{display}</span>'

        elif role == self.RAW_VALUE_ROLE:
            return value  # Actual raw value used for comparisons
        return None

    def set_dark_mode(self, enabled: bool):
        self._dark_mode = enabled
        self.layoutChanged.emit()

    def headerData(self, section, orientation, role=Qt.DisplayRole) -> Any:
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._headers[section]
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def is_dirty(self) -> bool:
        return self._dirty

    def is_backup_dirty(self) -> bool:
        return self._backup_dirty

    def mark_clean(self) -> None:
        self._dirty = False

    def mark_backup_clean(self) -> None:
        self._backup_dirty = False

    def finalize_save(self) -> None:
        """Mark state as clean and reset undo history to this point."""
        try:
            self.mark_clean()
            if self.undo_stack:
                self.undo_stack.clear()
            if self.redo_stack:
                self.redo_stack.clear()
            if self.unsaved_action_stack:
                self.unsaved_action_stack.clear()
            if self.undo_log_path.exists():
                self.undo_log_path.unlink()
        except Exception as e:
            logger.warning(f"Failed to finalize save: {e}")

    def setData(
        self, index: QModelIndex, value: Any, role=Qt.EditRole
    ) -> bool:
        if index.isValid() and role == Qt.EditRole:
            row, column = index.row(), index.column()
            current_value = self._data[row][column]

            if current_value == value:
                return False  # No change → no dirty flag

            # Inside setData (after verifying data has changed):
            action = Action(index.row(), index.column(), current_value, value)
            self.undo_stack.append(action)
            self.redo_stack.clear()
            # After pushing action
            self.unsaved_action_stack.append(action)
            self.stack_changed.emit()

            self._data[row][column] = value
            self._dirty = True
            self._backup_dirty = True
            self.dataChanged.emit(index, index)
            # Let auto-save handle the actual save
            return True
        return False

    def update_data(self, new_data) -> None:
        self.beginResetModel()
        self._raw_data = new_data or []
        self._data = [
            [item.get(header, "") for header in self._headers]
            for item in self._raw_data
        ]
        self.layoutChanged.emit()
        self.endResetModel()

    def get_current_data_as_dicts(self) -> list[dict]:
        return [
            {self._headers[i]: row[i] for i in range(len(self._headers))}
            for row in self._data
        ]

    def undo(self) -> None:
        """Undo one step of recorded history."""

        try:
            if self.undo_stack:
                last = self.undo_stack.pop()
                if self.unsaved_action_stack:
                    self.unsaved_action_stack.pop()
                self._apply_action(last, undo=True)
                self.redo_stack.append(last)
                self.stack_changed.emit()

        except Exception as e:
            logger.warning(f"Undo failed: {e}")

    def redo(self) -> None:
        """Redo one step from the redo stack."""
        if not self.redo_stack:
            return
        try:
            action = self.redo_stack.pop()
            self._apply_action(action, undo=False)
            self.undo_stack.append(action)
            self.unsaved_action_stack.append(action)
            self.stack_changed.emit()

        except Exception as e:
            logger.warning(f"Redo failed: {e}")

    def _apply_action(self, action, undo=True):
        value = action.old_value if undo else action.new_value
        self._data[action.row][
            action.column
        ] = value  # Update the data directly

        # Notify the view
        index = self.index(action.row, action.column)
        self.dataChanged.emit(index, index, [Qt.DisplayRole])

    def write_recovery_log_to_file(self):
        with open(self.undo_log_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "version": 1,
                    "unsaved_action_stack": [
                        a.__dict__ for a in self.unsaved_action_stack
                    ],
                    "undo_stack": [a.__dict__ for a in self.undo_stack],
                    "redo_stack": [a.__dict__ for a in self.redo_stack],
                },
                f,
                indent=2,
            )

    def load_undo_stack_from_file(self):
        with open(self.undo_log_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.unsaved_action_stack = [
                Action(**entry)
                for entry in data.get("unsaved_action_stack", [])
            ]

    def replay_undo_stack(self) -> None:
        """Replay stack to restore undo state from disk or memory."""
        try:
            for action in self.unsaved_action_stack:
                self._apply_action(action, undo=False)
        except Exception as e:
            print("Corrupted log: ", e)

    def prompt_user_for_recovery(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Question)
        msg.setWindowTitle("Recovery Available")
        msg.setText(
            "It looks like the application closed before the last session"
            + " could autosave.\n\nWould you like to load your most recent"
            + " unsaved changes?"
        )
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        return msg.exec_() == QMessageBox.Yes

    def update_sort_column_from_cache(self):
        """Update the sort column based on the cached sort key."""
        if self._proxy_model and self._proxy_model.sort_key_cache:
            for row_idx, value in self._proxy_model.sort_key_cache.items():
                if 0 <= row_idx < len(self._data):
                    self._data[row_idx][-1] = str(value)
