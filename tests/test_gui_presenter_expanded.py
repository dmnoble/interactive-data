import pytest
from unittest.mock import patch, MagicMock
from PyQt5.QtWidgets import QTableView
from PyQt5.QtCore import QObject, pyqtSignal, Qt
from src.gui_presenter import GuiPresenter
from PyQt5.QtCore import QAbstractTableModel


class DummyProxyModel(QAbstractTableModel):
    sortKeyChanged = pyqtSignal(str)
    filterExprChanged = pyqtSignal(str)
    filterCaseChanged = pyqtSignal(bool)
    filter_expr = "some_expr"
    case_sensitive = True
    custom_sort_key = "some_sort_key"

    def __init__(self):
        super().__init__()

    def rowCount(self, parent=None):
        return 0

    def columnCount(self, parent=None):
        return 0

    def data(self, index, role=Qt.DisplayRole):
        return None

    def set_filter_expression(self, expr):
        pass

    def set_case_sensitive(self, is_sensitive):
        pass

    def set_custom_sort_key(self, key):
        pass


class DummyController(QObject):
    profileNameChanged = pyqtSignal(str)
    viewNameChanged = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.proxy_model = DummyProxyModel()

    def check_dirty_and_save(self):
        pass

    def auto_backup_if_needed(self):
        pass

    def undo(self):
        pass

    def redo(self):
        pass

    def get_current_profile(self):
        return "test_profile"

    def get_current_view(self):
        return "test_view"

    def load_profile(self, profile_name):
        pass

    def load_view_config(self, view_name):
        pass

    def save_view_config(self, view_name):
        pass

    def set_default_view(self, view_name):
        pass

    def get_profiles(self):
        return ["TestProfile"]

    def save_theme_to_config(self, is_dark):
        pass  # no-op for test

    def get_all_view_names(self):
        return ["My View"]

    def get_default_view_name(self):
        return "My View"

    def set_default_view_name(self, view_name):
        pass


@pytest.fixture
def controller_mock():
    return DummyController()


@pytest.fixture
def gui_mock():
    gui = MagicMock()
    gui.profile_selector.currentText.return_value = "test_profile"
    gui.view_selector.currentText.return_value = "test_view"
    gui.custom_filter_input.text.return_value = "some_expr"
    gui.custom_sort_input.currentText.return_value = "some_key"
    gui.case_checkbox.isChecked.return_value = True
    return gui


@pytest.fixture
def table_view():
    return QTableView()


@pytest.fixture
def gui_presenter(controller_mock, gui_mock, table_view):
    return GuiPresenter(controller_mock, gui_mock, table_view)


def test_view_selector_with_valid_default_in_list(
    gui_presenter, controller_mock, gui_mock
):
    # Arrange
    view_names = ["view1", "view2", "default_view"]
    default_view = "default_view"

    controller_mock.get_all_view_names = lambda: view_names
    controller_mock.get_default_view_name = lambda: default_view

    # Act
    gui_presenter.view_selector_populate_set_to_default()

    # Assert: Calls refresh with expected view list and default
    gui_mock.refresh_view_selector.assert_called_once_with(
        view_names, default_view
    )


@pytest.fixture(autouse=True)
def patch_qshortcut(monkeypatch):
    _registry = []  # 👈 keep strong refs here

    class DummyShortcut(QObject):
        activated = pyqtSignal()

        def __init__(self, *args, **kwargs):
            super().__init__()  # no parent → simple, safe
            _registry.append(self)  # 👈 prevent GC

    monkeypatch.setattr("src.gui_presenter.QShortcut", DummyShortcut)


def test_init_sets_up_table_view_and_profiles(gui_presenter, gui_mock):
    gui_mock.profile_selector.setCurrentText.assert_not_called()
    gui_mock.view_selector.setCurrentText.assert_not_called()


def test_view_selector_populate_set_to_default(
    gui_presenter, controller_mock, gui_mock
):
    # Arrange
    view_names = ["view1", "view2"]
    default_view = "view1"

    controller_mock.get_all_view_names = lambda: view_names
    controller_mock.get_default_view_name = lambda: default_view

    # Act
    gui_presenter.view_selector_populate_set_to_default()

    # Assert: GUI was asked to refresh view selector correctly
    gui_mock.refresh_view_selector.assert_called_once_with(
        view_names, default_view
    )


def test_view_selector_with_empty_or_missing_default(
    gui_presenter, controller_mock, gui_mock
):
    # Arrange
    controller_mock.get_all_view_names = lambda: []
    controller_mock.get_default_view_name = lambda: "nonexistent"

    # Act
    gui_presenter.view_selector_populate_set_to_default()

    # Assert: refresh_view_selector called with expected values
    gui_mock.refresh_view_selector.assert_called_once_with([], "nonexistent")


def test_view_selector_with_default_missing_from_list(
    gui_presenter, controller_mock, gui_mock
):
    # Arrange
    view_names = ["view1", "view2"]
    default_view = "nonexistent_view"  # Not in the list

    controller_mock.get_all_view_names = lambda: view_names
    controller_mock.get_default_view_name = lambda: default_view

    # Act
    gui_presenter.view_selector_populate_set_to_default()

    # Assert: Still uses default_view, even if it’s missing
    gui_mock.refresh_view_selector.assert_called_once_with(
        view_names, default_view
    )


def test_set_auto_saves_starts_timers(gui_presenter):
    assert gui_presenter.auto_save_timer.isActive()
    assert gui_presenter.save_timer.isActive()
    assert gui_presenter.backup_timer.isActive()


def test_on_save_current_view_calls_controller(
    monkeypatch, gui_presenter, controller_mock, gui_mock
):
    called = {}

    def mock_save_current_view(
        name, custom_expr, case_sensitive, sort_column, sort_key, ascending
    ):
        called["name"] = name
        called["custom_expr"] = custom_expr
        called["case_sensitive"] = case_sensitive
        called["sort_column"] = sort_column
        called["sort_key"] = sort_key
        called["ascending"] = ascending

    controller_mock.save_current_view = mock_save_current_view

    # Full patch of QInputDialog so instantiation is avoided entirely
    with patch("src.gui_presenter.QInputDialog") as mock_dialog:
        instance = mock_dialog.return_value
        instance.exec_.return_value = True
        instance.textValue.return_value = (
            "My View"  # <- This is the actual fix
        )

        # Mock GUI elements
        gui_mock.sort_order_selector.currentText.return_value = "Asc"
        gui_mock.view_selector.clear.return_value = None
        gui_mock.view_selector.addItems.return_value = None
        gui_mock.set_view_selector.return_value = None
        gui_mock.get_current_view_name.return_value = "My View"

        gui_presenter.on_save_current_view()

    assert called["name"] == "My View"
    assert called["ascending"] is True


def test_on_set_default_view_calls_controller(
    monkeypatch, gui_presenter, controller_mock, gui_mock
):
    called = {}

    def mock_set_default(view_name):
        called["default"] = view_name

    controller_mock.set_default_view = mock_set_default

    # Mock returns a real string so .replace(...) works properly
    gui_mock.get_current_view_name.return_value = "My View (default)"

    gui_presenter.on_set_default_view()

    assert called["default"] == "My View"


def test_apply_structured_filter_sets_expression(
    controller_mock, gui_presenter, gui_mock
):
    controller_mock.proxy_model.set_filter_expression = MagicMock()

    # Simulate what happens *after* on_apply_structured_filter is called
    gui_mock.on_apply_structured_filter.return_value = None
    gui_mock.custom_filter_input.text.return_value = "age == 30"

    gui_presenter.apply_structured_filter()

    controller_mock.proxy_model.set_filter_expression.assert_called_with(
        "age == 30"
    )


def test_view_selector_populate_calls_refresh(
    gui_presenter, gui_mock, controller_mock
):
    controller_mock.get_all_view_names = lambda: ["v1", "v2"]
    controller_mock.get_default_view_name = lambda: "v1"

    gui_presenter.view_selector_populate_set_to_default()

    gui_mock.refresh_view_selector.assert_called_with(["v1", "v2"], "v1")
