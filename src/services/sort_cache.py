from typing import Optional


class SortCacheHelper:
    @staticmethod
    def apply_sort_cache_to_model(
        model,
        sort_key_cache: dict[int, str],
        sort_column: Optional[int] = None,
    ) -> None:
        if sort_column is None:
            sort_column = model.columnCount() - 1
        if not model:
            return

        for row_idx, value in sort_key_cache.items():
            if 0 <= row_idx < len(model._data):
                model._raw_data[row_idx]["sort_key"] = str(value)
                model._data[row_idx][sort_column] = str(value)
                index = model.index(row_idx, sort_column)
                model.dataChanged.emit(index, index)

    @staticmethod
    def clear_sort_column(model, sort_column: Optional[int] = None) -> None:
        if sort_column is None:
            sort_column = model.columnCount() - 1
        if not model:
            return

        sort_column = model.columnCount() - 1
        for row_idx in range(len(model._data)):
            model._data[row_idx][sort_column] = ""
            index = model.index(row_idx, sort_column)
            model.dataChanged.emit(index, index)
