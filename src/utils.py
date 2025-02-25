from datetime import datetime


def format_date(date_string):
    """
    Converts a date string (YYYY-MM-DD) into a readable format (e.g., 'October
    12, 2023').
    """
    try:
        return datetime.strptime(date_string, "%Y-%m-%d").strftime("%B %d, %Y")
    except ValueError:
        return "Invalid date format"


def multi_sort(data, sort_keys):
    """
    Sorts a list of dictionaries based on multiple keys.

    :param data: List of dictionaries
    :param sort_keys: List of keys to sort by (in priority order)
    :return: Sorted list of dictionaries
    """
    return sorted(data, key=lambda x: tuple(x.get(k, "") for k in sort_keys))


def validate_input(value, expected_type):
    """
    Validates user input based on expected type.

    :param value: The value to check
    :param expected_type: The type the value should be (str, int, float, etc.)
    :return: Boolean indicating validity
    """
    try:
        expected_type(value)
        return True
    except ValueError:
        return False


def remove_duplicates(data_list):
    """
    Removes duplicates from a list while preserving order.

    :param data_list: List with possible duplicate values
    :return: List with unique values
    """
    seen = set()
    return [x for x in data_list if not (x in seen or seen.add(x))]


def get_current_timestamp():
    """
    Returns the current timestamp in YYYY-MM-DD HH:MM:SS format.
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
