from typing import Optional, Any
from datetime import datetime
from PyQt5.QtCore import QDateTime


def format_date(date_string: str) -> str:
    """
    Converts a date string (YYYY-MM-DD) into a readable format.
    Example: '2023-10-12' → 'October 12, 2023'
    """
    try:
        return datetime.strptime(date_string, "%Y-%m-%d").strftime("%B %d, %Y")
    except ValueError:
        return "Invalid date format"


def multi_sort(data: list[dict], sort_keys: list[str]) -> list[dict]:
    """
    Sorts a list of dictionaries by multiple keys in order of priority.
    """
    return sorted(data, key=lambda x: tuple(x.get(k, "") for k in sort_keys))


def validate_input(value: Any, expected_type: type) -> bool:
    """
    Validates that a value can be cast to the expected type.
    """
    try:
        expected_type(value)
        return True
    except ValueError:
        return False


def remove_duplicates(data_list):
    """
    Removes duplicates from a list while preserving order.
    """
    seen = set()
    return [x for x in data_list if not (x in seen or seen.add(x))]


def get_current_timestamp() -> str:
    """
    Returns the current timestamp in YYYY-MM-DD HH:MM:SS format.
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_save_time_label_text(
    last_save_time: QDateTime, current_time: Optional[QDateTime] = None
) -> str:
    """
    Returns a human-readable label showing time since last save.
    """
    current_time = current_time or QDateTime.currentDateTime()
    minutes = last_save_time.secsTo(current_time) // 60
    if minutes == 0:
        return "Last saved: just now"
    elif minutes == 1:
        return "Last saved: 1 minute ago"
    else:
        return f"Last saved: {minutes} minutes ago"
