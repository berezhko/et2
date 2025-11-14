import pandas
from os.path import basename


class Compare:
    def __init__(self, left_file, right_file, sort_array, columns, suffix=basename):
        self._sort_array = sort_array
        self._columns = columns
        self._merge = self._merge_data(
            self._read_scheme(left_file),
            self._read_scheme(right_file),
            suffix(left_file),
            suffix(right_file),
        )

    def _read_scheme(self, file_name):
        return pandas.DataFrame(
            pandas.read_csv(file_name, dtype=str, keep_default_na=False).sort_values(
                self._sort_array
            ),
            columns=self._columns,
        )

    def _merge_data(self, left_df, right_df, left_suffix, right_suffix):
        result = (
            left_df.merge(right_df, how="outer", suffixes=["", "_"], indicator=True)
            .loc[lambda x: x["_merge"] != "both"]
            .sort_values(self._sort_array)
        )
        result["_merge"] = result["_merge"].cat.rename_categories(
            {"left_only": left_suffix}
        )
        result["_merge"] = result["_merge"].cat.rename_categories(
            {"right_only": right_suffix}
        )
        result.index = range(1, len(result.index) + 1)
        return result

    def diff(self):
        return self._merge

    def select_columns(self, key, columns):
        return pandas.DataFrame(
            self._merge[self._merge["Имя"] == key], columns=["_merge"] + columns[key]
        )
