"""Data processing module — deliberately undocumented functions.

This sample has NO docstrings on any function, so IntelliDoc should flag
every function with NO_DOCSTRING findings and yield a very low score.
"""


def load_csv(file_path, delimiter=",", encoding="utf-8"):
    rows = []
    with open(file_path, "r", encoding=encoding) as f:
        header = f.readline().strip().split(delimiter)
        for line in f:
            values = line.strip().split(delimiter)
            rows.append(dict(zip(header, values)))
    return rows


def filter_rows(data, column, value):
    return [row for row in data if row.get(column) == value]


def aggregate(data, column, operation="sum"):
    values = [float(row[column]) for row in data if column in row]
    if operation == "sum":
        return sum(values)
    elif operation == "avg":
        return sum(values) / len(values) if values else 0
    elif operation == "min":
        return min(values) if values else None
    elif operation == "max":
        return max(values) if values else None
    return None


def sort_data(data, key, reverse=False):
    return sorted(data, key=lambda row: row.get(key, ""), reverse=reverse)


def deduplicate(data, key):
    seen = set()
    unique = []
    for row in data:
        val = row.get(key)
        if val not in seen:
            seen.add(val)
            unique.append(row)
    return unique


def export_json(data, output_path, indent=2):
    import json
    with open(output_path, "w") as f:
        json.dump(data, f, indent=indent)


def transform_keys(data, mapping):
    result = []
    for row in data:
        new_row = {}
        for old_key, new_key in mapping.items():
            if old_key in row:
                new_row[new_key] = row[old_key]
        result.append(new_row)
    return result


def pivot_table(data, index_col, value_col, agg_func="sum"):
    pivot = {}
    for row in data:
        key = row.get(index_col)
        val = float(row.get(value_col, 0))
        if key not in pivot:
            pivot[key] = []
        pivot[key].append(val)

    result = {}
    for key, values in pivot.items():
        if agg_func == "sum":
            result[key] = sum(values)
        elif agg_func == "avg":
            result[key] = sum(values) / len(values)
        elif agg_func == "count":
            result[key] = len(values)
    return result
