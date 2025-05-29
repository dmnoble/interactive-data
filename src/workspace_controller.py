# workspace_controller.py

from pathlib import Path
import logging
from typing import Optional, cast
import os
from data_manager import DataManager
from table_model import DataTableModel
from config_manager import ConfigManager
from view_config_service import ViewConfigService

logger = logging.getLogger(__name__)


class WorkspaceController:
    # Directory to store user configs
    CONFIG_DIR = Path("config_profiles")
    CONFIG_END = "_config.json"

    def __init__(self) -> None:
        self.profile_name: str = ""
        self.data_manager = DataManager()
        self.config: Optional[ConfigManager] = None
        self.model: Optional[DataTableModel] = None

    @property
    def require_model(self) -> DataTableModel:
        assert self.model is not None, "Model not loaded"
        return cast(DataTableModel, self.model)

    @property
    def require_config(self) -> ConfigManager:
        assert self.config is not None, "Config must be loaded before use"
        return cast(ConfigManager, self.config)

    def undo(self) -> None:
        """Undo the last action in the model."""
        self.require_model.undo()

    def redo(self) -> None:
        self.require_model.redo()

    def load_profile(self, new_profile_name: str) -> Optional[ConfigManager]:
        if new_profile_name == self.profile_name:
            return None

        if self.profile_name:
            self.check_dirty_and_save()

        self.profile_name = new_profile_name
        self.config_path = (
            self.CONFIG_DIR / f"{self.profile_name}{self.CONFIG_END}"
        )
        self.config = ConfigManager(self.config_path)

        logger.info(f"Loaded profile: {self.profile_name}")
        return self.config

    def load_data(self, proxy_model) -> tuple[DataTableModel, list]:
        # Load real data from DataManager
        raw_data = self.data_manager.load_data(self.profile_name)

        # Dynamically get headers from first item (or fallback)
        headers = list(raw_data[0].keys()) if raw_data else []

        # Create the model
        self.model = DataTableModel(
            raw_data,
            headers,
            data_manager=self.data_manager,
            proxy_model=proxy_model,
            dark_mode=self.require_config.is_dark_mode(),
        )
        return self.model, headers

    def check_dirty_and_save(self) -> None:
        if self.model and self.model.is_dirty():
            try:
                data = self.model.get_current_data_as_dicts()
                self.data_manager.save_data(data, self.profile_name)
                self.model.finalize_save()
                logger.info("Auto-save complete.")
            except Exception as e:
                logger.exception("Auto-save failed:", exc_info=e)

    def auto_backup_if_needed(self) -> None:
        """
        Auto-Backup every hour and on close
        """
        if self.model and self.model.is_backup_dirty():
            try:
                data = self.model.get_current_data_as_dicts()
                self.data_manager.save_backup(data, self.profile_name)
                self.model.mark_backup_clean()
                logger.info("Auto-backup successful.")
            except Exception as e:
                logger.warning("Auto-backup failed:", exc_info=e)

    def save_current_view(
        self,
        name: str,
        custom_expr: str,
        case_sensitive: bool,
        sort_column: int,
        field: str,
        operator: str,
        value: str,
        sort_key: str,
        ascending: bool,
    ) -> None:
        """Save current view settings under the given name."""

        config = {
            "name": name,
            "filter_text": custom_expr,
            "case_sensitive": case_sensitive,
            "sort_column": (sort_column),
            "ascending": ascending,
            "filter": {
                "field": field,
                "operator": operator,
                "value": value,
            },
            "custom_filter": custom_expr,
            "custom_sort_key": sort_key,
        }
        ViewConfigService.save_view(name, config, self.profile_name)

    def set_default_view(self, view_name: str) -> None:
        """Mark the given view as default for this profile."""
        ViewConfigService.set_default(view_name, self.profile_name)

    def get_default_view(self):
        return ViewConfigService.get_default(self.profile_name)

    def load_view_config(self, view_name: str) -> tuple[Optional[dict], int]:
        config = ViewConfigService.load_view(view_name, self.profile_name)

        if not config:  # If no config found, return None
            return None, 0

        self.require_model.update_sort_column_from_cache()
        sort_column = self.require_model.columnCount() - 1

        return config, sort_column

    def save_theme_to_config(self, is_dark):
        self.require_config.set_theme("Dark" if is_dark else "Light")
        self.require_model.set_dark_mode(is_dark)

    def apply_custom_sort(self, sort_key_cache) -> list:
        # 🛠 Inject sort result values directly into DataTableModel
        if self.model:
            for row_idx, sort_value in sort_key_cache.items():
                if 0 <= row_idx < len(self.model._data):
                    self.model._data[row_idx][-1] = str(sort_value)

        # ✅ Visually apply saved sort direction (fallback)
        headers = self.require_model._headers
        return headers

    def clear_custom_sort(self) -> None:
        if self.model:
            sort_column = self.model.columnCount() - 1
            for row_index in range(len(self.model._data)):
                self.model._data[row_index][sort_column] = ""
                index = self.model.index(row_index, sort_column)
                self.model.dataChanged.emit(index, index)

    def update_filter_operators(self, field: str, raw_value_role: int) -> str:
        sample_value = ""
        headers = self.require_model._headers
        if field in headers:
            col_index = headers.index(field)
            for row in range(self.require_model.rowCount()):
                index = self.require_model.index(row, col_index)
                value = self.require_model.data(index, raw_value_role)
                if value is not None:
                    sample_value = value
                    break
        return sample_value

    def get_profiles(self):
        """Returns a list of available profiles based on config files."""
        if not os.path.exists(self.CONFIG_DIR):
            os.makedirs(self.CONFIG_DIR)
        return [
            f.replace(self.CONFIG_END, "")
            for f in os.listdir(self.CONFIG_DIR)
            if f.endswith(self.CONFIG_END)
        ]

    def get_all_view_names(self) -> list:
        """Get all view names for the current profile."""
        return ViewConfigService.list_views(self.profile_name)

    def get_default_view_name(self) -> Optional[str]:
        """Get the default view name for the current profile."""
        return ViewConfigService.get_default(self.profile_name)

    def create_profile(self, profile_name: str) -> bool:
        """
        Create a new profile config and associated empty data file.
        Returns True if profile was created, False if it already existed.
        """
        existing = profile_name in self.get_profiles()
        if existing:
            return False

        # Create default config and empty data file
        self.load_profile(profile_name)
        self.data_manager.save_data([], profile_name)
        return True
