from src.utils import format_date, multi_sort


def test_format_date():
    """Test date formatting function."""
    assert format_date("2023-10-12") == "October 12, 2023"


def test_multi_sort():
    """Test sorting multiple keys."""
    data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
    sorted_data = multi_sort(data, ["age"])
    assert sorted_data[0]["name"] == "Bob"  # Youngest should be first
