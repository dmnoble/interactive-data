# data_manager.py
from pathlib import Path
import json
import time
from logger import setup_logger
from typing import List

logger = setup_logger("data_manager")
MAX_BACKUPS = 10  # set your cap here


CONFIG_DIR = Path("config_profiles")
CONFIG_END = "_data.json"
BACKUP_DIR = Path("backups")
MAX_BACKUPS = 10


class DataManager:
    """
    Manages loading, saving, and backing up user data.
    """

    def get_config_path(self, profilename: str) -> Path:
        """Returns the config file path for a specific profile."""
        return CONFIG_DIR / f"{profilename}{CONFIG_END}"

    def load_data(self, profilename: str = "default") -> List[dict]:
        """
        Load data from the specified file.
        """
        path = self.get_config_path(profilename)
        if not path.exists():
            return []
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
                if (
                    isinstance(data, list)
                    and data
                    and isinstance(data[0], dict)
                ):
                    return data
                logger.warning(
                    "Unexpected data format; expected a list of dicts."
                )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from {path}: {e}")
        return []

    def save_data(
        self, data: List[dict], profilename: str = "default"
    ) -> None:
        """Save data to the specified file, with retry logic."""
        if not data:
            return

        path = self.get_config_path(profilename)
        # Retry logic
        max_attempts = 3
        delay_seconds = 0.5

        for attempt in range(1, max_attempts + 1):
            try:
                with path.open("w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                logger.info(f"Data saved to {path} on attempt {attempt}")
                return  # success!
            except IOError as e:
                logger.warning(f"Save attempt {attempt} failed: {e}")
                time.sleep(delay_seconds)

        logger.error("All save attempts failed.")
        raise IOError("Failed to save data after multiple attempts.")

    def save_backup(
        self, data: List[dict], profilename: str = "default"
    ) -> None:
        """Save a timestamped backup of the data and prune old backups."""
        BACKUP_DIR.mkdir(exist_ok=True)

        src_filename = self.get_config_path(profilename).name
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        backup_file = BACKUP_DIR / f"{src_filename}.{timestamp}.bak"

        try:
            with backup_file.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Backup saved to {backup_file}")
        except Exception as e:
            logger.warning(f"Failed to save backup to {backup_file}: {e}")

        # Prune old backups
        backups = sorted([f for f in BACKUP_DIR.glob(f"{src_filename}.*.bak")])

        while len(backups) > MAX_BACKUPS:
            old_backup = backups.pop(0)
            try:
                old_backup.unlink()
                logger.info(f"Old backup removed: {old_backup}")
            except Exception as e:
                logger.warning(
                    f"Failed to remove old backup {old_backup}: {e}"
                )
