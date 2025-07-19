from src.table_model import DataTableModel
from src.undo_redo import Action
import pytest
from pathlib import Path


@pytest.fixture(autouse=True)
def delete_test_profile_json():
    yield
    (Path.cwd() / ".undo_log.json").unlink(missing_ok=True)


def test_undo_redo_operations():
    headers = ["name", "role"]
    data = [{"name": "Alice", "role": "Engineer"}]
    model = DataTableModel(data.copy(), headers)

    index = model.index(0, 0)
    new_value = "Alicia"

    # Perform edit
    model.setData(index, new_value)
    assert model._data[0][0] == "Alicia"

    # Undo it
    model.undo()
    assert model._data[0][0] == "Alice"

    # Redo it
    model.redo()
    assert model._data[0][0] == "Alicia"


def test_undo_stack_clears_on_new_edit():
    headers = ["name"]
    data = [{"name": "Alice"}]
    model = DataTableModel(data.copy(), headers)

    index = model.index(0, 0)
    model.setData(index, "Alicia")
    model.undo()
    assert model._data[0][0] == "Alice"

    model.setData(index, "Ally")  # new edit after undo
    assert len(model.redo_stack) == 0  # redo stack should be cleared


def test_action_description_generates_human_readable_output():
    action = Action(row=1, column=2, old_value="Bob", new_value="Robert")
    description = action.description()
    assert description == "Edited (1, 2): 'Bob' → 'Robert'"


def test_action_properties():
    action = Action(row=0, column=1, old_value="Old", new_value="New")
    assert action.row == 0
    assert action.column == 1
    assert action.old_value == "Old"
    assert action.new_value == "New"
