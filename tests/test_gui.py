import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTableView
from src.gui.main_window import BuildGui


@pytest.fixture
def gui(qtbot):
    table_view = QTableView()
    widget = BuildGui(table_view)
    qtbot.addWidget(widget)
    return widget


def test_gui_initializes_and_has_core_widgets(gui):
    assert gui.windowTitle() == "Interactive Data Workspace"
    assert gui.profile_label.text() == "Select Profile:"
    assert gui.profile_selector.count() == 0

    items = [
        gui.theme_selector.itemText(i)
        for i in range(gui.theme_selector.count())
    ]
    assert "Light" in items
    assert "Dark" in items

    assert gui.custom_expr_help_button.text() == "?"
    assert gui.custom_sort_help_button.text() == "?"
    assert gui.custom_filter_input is not None
    assert gui.field_selector is not None
    assert gui.custom_sort_input.isEditable()


def test_gui_help_buttons_trigger_slots(qtbot, gui, monkeypatch):
    called_filter = {}
    called_sort = {}

    monkeypatch.setattr(
        gui,
        "show_filter_expr_help",
        lambda: called_filter.setdefault("called", True),
    )
    monkeypatch.setattr(
        gui,
        "show_sort_expr_help",
        lambda: called_sort.setdefault("called", True),
    )

    gui.custom_expr_help_button.clicked.disconnect()
    gui.custom_expr_help_button.clicked.connect(gui.show_filter_expr_help)
    gui.custom_sort_help_button.clicked.disconnect()
    gui.custom_sort_help_button.clicked.connect(gui.show_sort_expr_help)

    qtbot.mouseClick(gui.custom_expr_help_button, Qt.LeftButton)
    qtbot.mouseClick(gui.custom_sort_help_button, Qt.LeftButton)

    assert called_filter.get("called") is True
    assert called_sort.get("called") is True


def test_gui_filter_placeholder(gui):
    placeholder = gui.custom_filter_input.placeholderText()
    assert "Custom Filter Expression" in placeholder


def test_gui_sort_placeholder(gui):
    placeholder = gui.custom_sort_input.lineEdit().placeholderText()
    assert "Enter Custom Sort Key" in placeholder


def test_gui_refresh_view_selector_marks_default(gui):
    gui.refresh_view_selector(
        ["a", "b", "default_view"], default_name="default_view"
    )
    texts = [
        gui.view_selector.itemText(i) for i in range(gui.view_selector.count())
    ]
    assert "default_view (default)" in texts
    assert "a" in texts
    assert "b" in texts


def test_gui_update_undo_redo_history(gui):
    class FakeAction:
        def __init__(self, name):
            self._name = name

        def description(self):
            return self._name

    undo_stack = [FakeAction("Undo A"), FakeAction("Undo B")]
    redo_stack = [FakeAction("Redo X"), FakeAction("Redo Y")]

    gui.update_undo_redo_history(undo_stack, redo_stack)

    undo_items = [
        gui.undo_history_combo.itemText(i)
        for i in range(gui.undo_history_combo.count())
    ]
    redo_items = [
        gui.redo_history_combo.itemText(i)
        for i in range(gui.redo_history_combo.count())
    ]

    assert undo_items == ["Undo B", "Undo A"]
    assert redo_items == ["Redo Y", "Redo X"]


def test_gui_on_apply_structured_filter_adds_expression(gui):
    gui.field_selector.addItem("priority")
    gui.field_selector.setCurrentText("priority")
    gui.operator_selector.addItem(">=")
    gui.operator_selector.setCurrentText(">=")
    gui.value_input.setText("5")

    gui.custom_filter_input.setText("")
    gui.on_apply_structured_filter()

    assert gui.custom_filter_input.text() == "priority >= 5"
