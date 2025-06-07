from typing import Any, Dict, Optional
from view_config import (
    save_view_config,
    get_view_config,
    set_default_view,
    get_default_view_name,
    get_all_view_names,
)


class ViewConfigService:
    @staticmethod
    def save_view(
        name: str, config: Dict[str, Any], profile_name: str
    ) -> None:
        save_view_config(name, config, profile_name)

    @staticmethod
    def load_view(name: str, profile_name: str) -> Optional[Dict[str, Any]]:
        return get_view_config(name, profile_name)

    @staticmethod
    def set_default(name: str, profile_name: str) -> None:
        set_default_view(name, profile_name)

    @staticmethod
    def get_default(profile_name: str) -> Optional[str]:
        return get_default_view_name(profile_name)

    @staticmethod
    def list_views(profile_name: str) -> list[str]:
        return get_all_view_names(profile_name)
