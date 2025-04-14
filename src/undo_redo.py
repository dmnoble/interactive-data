from dataclasses import dataclass
from typing import Any


@dataclass
class Action:
    row: int
    column: int
    old_value: Any
    new_value: Any

    def description(self) -> str:
        return (
            f"Edited ({self.row}, {self.column}): '{self.old_value}' →"
            + f"'{self.new_value}'"
        )
