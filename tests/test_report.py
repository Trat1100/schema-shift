import json

from schemashift.report import render_json, render_text


def test_json_report_is_stable_and_contains_only_schema_findings():
    source = {"schema": "main", "tables": {}}
    target = {"schema": "main", "tables": {"users": {"columns": {}}}}
    findings = [{"kind": "table_only_in_target", "table": "users"}]
    report = json.loads(render_json(source, target, findings))
    assert report["status"] == "drift"
    assert report["finding_count"] == 1
    assert render_text(source, target, findings) == "Schema drift detected: 1 finding(s).\n- users: table only in target"
