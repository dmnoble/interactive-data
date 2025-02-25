# data_manager.py
import json


class DataManager:
    def __init__(self, file_path="data.json"):
        self.file_path = file_path

    def load_data(self):
        try:
            with open(self.file_path, "r") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_data(self, data):
        with open(self.file_path, "w") as file:
            json.dump(data, file, indent=4)

    def backup_data(self, backup_path="backup.json"):
        data = self.load_data()
        with open(backup_path, "w") as file:
            json.dump(data, file, indent=4)
        print("Backup saved successfully.")
