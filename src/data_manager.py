# data_manager.py
import json
from logger import setup_logger

logger = setup_logger("data_manager")


class DataManager:
    """
    Manages loading, saving, and backing up user data.

    Attributes:
        file_path (str): The path to the data file.
    """

    def __init__(self, file_path="data.json"):
        self.file_path = file_path

    def load_data(self):
        """
        Load data from the specified file.

        Returns:
            dict: The data loaded from the file.
        """
        try:
            with open(self.file_path, "r") as f:
                data = json.load(f)
                if isinstance(data, list) and isinstance(data[0], dict):
                    return data
                else:
                    # Fallback or error handling
                    print("Unexpected data format")
                    return []
        except FileNotFoundError:
            return []

    def save_data(self, data):
        """
        Save data to the specified file.

        Parameter:
            data (dict): The data to save.
        """
        with open(self.file_path, "w") as file:
            json.dump(data, file, indent=4)

    def backup_data(self, backup_path="backup.json"):
        """
        Save data to a backup data file.

        Returns:
            data (dict): The data to save.
        """
        data = self.load_data()
        with open(backup_path, "w") as file:
            json.dump(data, file, indent=4)
        print("Backup saved successfully.")
