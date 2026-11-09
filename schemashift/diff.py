from __future__ import annotations


def compare_snapshots(source: dict, target: dict) -> list[dict]:
    findings: list[dict] = []
    source_tables = source["tables"]
    target_tables = target["tables"]

    for table_name in sorted(source_tables.keys() - target_tables.keys()):
        findings.append({"kind": "table_missing_from_target", "table": table_name})
    for table_name in sorted(target_tables.keys() - source_tables.keys()):
        findings.append({"kind": "table_only_in_target", "table": table_name})

    for table_name in sorted(source_tables.keys() & target_tables.keys()):
        left = source_tables[table_name]
        right = target_tables[table_name]
        left_columns = left["columns"]
        right_columns = right["columns"]
        for column_name in sorted(left_columns.keys() - right_columns.keys()):
            findings.append({"kind": "column_missing_from_target", "table": table_name, "column": column_name})
        for column_name in sorted(right_columns.keys() - left_columns.keys()):
            findings.append({"kind": "column_only_in_target", "table": table_name, "column": column_name})

        for column_name in sorted(left_columns.keys() & right_columns.keys()):
            for field in ("type", "nullable", "has_default"):
                before = left_columns[column_name][field]
                after = right_columns[column_name][field]
                if before != after:
                    findings.append(
                        {
                            "kind": "column_changed",
                            "table": table_name,
                            "column": column_name,
                            "field": field,
                            "source": before,
                            "target": after,
                        }
                    )

        for field, kind in (
            ("primary_key", "primary_key_changed"),
            ("foreign_keys", "foreign_keys_changed"),
            ("unique_constraints", "unique_constraints_changed"),
            ("indexes", "indexes_changed"),
        ):
            if left[field] != right[field]:
                findings.append({"kind": kind, "table": table_name, "source": left[field], "target": right[field]})

    return findings
