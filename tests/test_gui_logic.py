from PyQt5.QtCore import QDateTime
from src.utils import get_save_time_label_text


def test_get_save_time_label_text():
    last_saved = QDateTime.currentDateTime().addSecs(-120)
    now = QDateTime.currentDateTime()
    result = get_save_time_label_text(last_saved, now)
    assert result == "Last saved: 2 minutes ago"
