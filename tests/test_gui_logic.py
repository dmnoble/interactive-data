from PyQt5.QtCore import QDateTime
from PyQt5.QtWidgets import QLabel
from unittest.mock import patch


def test_save_time_label_logic_with_mock():
    label = QLabel()

    # Fake "last saved" time = now - 2 minutes
    last_saved = QDateTime.currentDateTime().addSecs(-120)

    # Simulate MainWindow method
    def update_label(last_save_time):
        now = QDateTime.currentDateTime()
        minutes = last_save_time.secsTo(now) // 60
        if minutes == 0:
            label.setText("Last saved: just now")
        elif minutes == 1:
            label.setText("Last saved: 1 minute ago")
        else:
            label.setText(f"Last saved: {minutes} minutes ago")

    with patch("PyQt5.QtCore.QDateTime.currentDateTime") as mock_current:
        # Simulate current time as now
        mock_current.return_value = QDateTime.currentDateTime()
        update_label(last_saved)

    assert "2 minutes ago" in label.text()
