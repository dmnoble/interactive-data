# data_manager.py
import os
import json
import time
from logger import setup_logger

logger = setup_logger("data_manager")
MAX_BACKUPS = 10  # set your cap here


CONFIG_DIR = "config_profiles"
CONFIG_END = "_data.json"


class DataManager:
    """
    Manages loading, saving, and backing up user data.

    Attributes:
        file_path (str): The path to the data file.
    """

    def get_config_path(self, profilename):
        """Returns the config file path for a specific profile."""
        return os.path.join(CONFIG_DIR, f"{profilename}{CONFIG_END}")

    def load_data(self, profilename="default"):
        """
        Load data from the specified file.

        Returns:
            dict: The data loaded from the file.
        """
        config_path = self.get_config_path(profilename)
        try:
            with open(config_path, "r") as f:
                data = json.load(f)
                if isinstance(data, list) and isinstance(data[0], dict):
                    return data
                else:
                    # Fallback or error handling
                    print("Unexpected data format")
                    return []
        except FileNotFoundError:
            return []

    def save_data(self, data, profilename="default"):
        """
        Save data to the specified file.

        Parameter:
            data (dict): The data to save.
        """
        # Retry logic
        max_attempts = 3
        delay_seconds = 0.5

        config_path = self.get_config_path(profilename)

        for attempt in range(1, max_attempts + 1):
            try:
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                logger.info(f"Data saved successfully on attempt {attempt}.")
                return  # success!
            except IOError as e:
                logger.warning(f"Save attempt {attempt} failed: {e}")
                time.sleep(delay_seconds)

        logger.error("All save attempts failed.")
        raise IOError("Failed to save data after multiple attempts.")

    def save_backup(self, data, profilename="default"):
        backup_dir = "backups"
        os.makedirs(backup_dir, exist_ok=True)

        config_path = self.get_config_path(profilename)

        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = os.path.basename(config_path)
        backup_path = os.path.join(backup_dir, f"{filename}.{timestamp}.bak")

        try:
            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Backup saved to {backup_path}")
        except Exception as e:
            logger.warning(f"Failed to save backup: {e}")

        # 🔁 Delete old backups if over cap
        backups = sorted(
            [
                os.path.join(backup_dir, f)
                for f in os.listdir(backup_dir)
                if f.startswith(filename) and f.endswith(".bak")
            ]
        )

        while len(backups) > MAX_BACKUPS:
            to_delete = backups.pop(0)
            try:
                os.remove(to_delete)
                logger.info(f"Old backup removed: {to_delete}")
            except Exception as e:
                logger.warning(f"Failed to remove old backup: {e}")
