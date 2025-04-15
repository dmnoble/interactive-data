import json
from src.table_model import DataTableModel
from src.undo_redo import Action


def test_unsaved_stack_written_correctly(tmp_path):
    headers = ["name"]
    data = [{"name": "Alice"}]
    model = DataTableModel(data.copy(), headers)
    model.undo_log_path = tmp_path / "test_log.json"

    index = model.index(0, 0)
    model.setData(index, "Alicia")

    with open(model.undo_log_path, "r", encoding="utf-8") as f:
        content = json.load(f)

    assert "unsaved_action_stack" in content
    assert content["unsaved_action_stack"][0]["new_value"] == "Alicia"
    assert content["undo_stack"][0]["new_value"] == "Alicia"
    assert content["redo_stack"] == []


def test_replay_unsaved_stack_restores_data(tmp_path):
    headers = ["name"]
    data = [{"name": "Alice"}]
    model = DataTableModel(data.copy(), headers)
    model.undo_log_path = tmp_path / "test_log.json"

    # Simulate prior actions
    action = Action(row=0, column=0, old_value="Alice", new_value="Alicia")
    model.unsaved_action_stack.append(action)
    model.write_recovery_log_to_file()

    # New model should load and apply
    new_model = DataTableModel(data.copy(), headers)
    new_model.undo_log_path = model.undo_log_path
    new_model.load_undo_stack_from_file()
    new_model.replay_undo_stack()

    assert new_model._data[0][0] == "Alicia"
