from PyQt5.QtCore import Qt
from filter_proxy import TableFilterProxyModel


class ProxyModelService:
    @staticmethod
    def apply_filter(
        proxy: TableFilterProxyModel, field: str, operator: str, value: str
    ) -> None:
        proxy.set_structured_filter(field, operator, value)

    @staticmethod
    def clear_filter(proxy: TableFilterProxyModel) -> None:
        proxy.set_structured_filter("", "==", "")

    @staticmethod
    def apply_custom_sort(
        proxy: TableFilterProxyModel, sort_key: str, ascending: bool
    ) -> tuple[int, Qt.SortOrder]:
        proxy.set_custom_sort_key(sort_key)
        proxy.rebuild_sort_key_cache()

        sort_column = proxy.sourceModel().columnCount() - 1
        sort_order = Qt.AscendingOrder if ascending else Qt.DescendingOrder

        return sort_column, sort_order

    @staticmethod
    def clear_custom_sort(proxy: TableFilterProxyModel) -> int:
        proxy.set_custom_sort_key("")
        proxy.sort_key_cache.clear()
        return proxy.sourceModel().columnCount() - 1
