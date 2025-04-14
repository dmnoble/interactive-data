from src.table_model import DataTableModel


def test_undo_redo_operations():
    headers = ["name", "role"]
    data = [{"name": "Alice", "role": "Engineer"}]  # ✅ dictionary
    model = DataTableModel(data.copy(), headers)

    index = model.index(0, 0)
    new_value = "Alicia"

    # Perform edit
    model.setData(index, new_value)
    assert model._data[0][0] == "Alicia"  # ✅ access processed list-of-lists

    # Undo it
    model.undo()
    assert model._data[0][0] == "Alice"

    # Redo it
    model.redo()
    assert model._data[0][0] == "Alicia"


def test_undo_stack_clears_on_new_edit():
    headers = ["name"]
    data = [{"name": "Alice"}]  # ✅ dictionary
    model = DataTableModel(data.copy(), headers)

    index = model.index(0, 0)
    model.setData(index, "Alicia")
    model.undo()
    assert model._data[0][0] == "Alice"

    model.setData(index, "Ally")  # new edit after undo
    assert len(model.redo_stack) == 0  # redo stack should be cleared
