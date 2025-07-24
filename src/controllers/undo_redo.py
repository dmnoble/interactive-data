from dataclasses import dataclass
from typing import Any


@dataclass
class Action:
    """Represents a user edit action for undo/redo support."""

    row: int
    column: int
    old_value: Any
    new_value: Any

    def description(self) -> str:
        """Return a human-readable description of the action."""
        return (
            f"Edited ({self.row}, {self.column}):"
            + f" '{self.old_value}' → '{self.new_value}'"
        )
