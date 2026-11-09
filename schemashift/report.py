from __future__ import annotations

import json


def render_json(source: dict, target: dict, findings: list[dict]) -> str:
    report = {
        "status": "drift" if findings else "clean",
        "source_schema": source["schema"],
        "target_schema": target["schema"],
        "finding_count": len(findings),
        "findings": findings,
    }
    return json.dumps(report, indent=2, sort_keys=True)


def render_text(source: dict, target: dict, findings: list[dict]) -> str:
    if not findings:
        return f"No schema drift detected ({len(source['tables'])} tables compared)."
    lines = [f"Schema drift detected: {len(findings)} finding(s)."]
    for finding in findings:
        kind = finding["kind"]
        table = finding.get("table", "")
        column = finding.get("column")
        location = ".".join(part for part in (table, column) if part)
        if kind == "column_changed":
            lines.append(f"- {location}: {finding['field']} differs (source={finding['source']!r}, target={finding['target']!r})")
        elif kind in {"foreign_keys_changed", "unique_constraints_changed", "indexes_changed", "primary_key_changed"}:
            lines.append(f"- {table}: {kind.replace('_', ' ')}")
        else:
            lines.append(f"- {location or table}: {kind.replace('_', ' ')}")
    return "\n".join(lines)
