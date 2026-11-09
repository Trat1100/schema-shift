from sqlalchemy import Column, ForeignKey, Integer, MetaData, String, Table, UniqueConstraint, create_engine

from schemashift.diff import compare_snapshots
from schemashift.reflect import reflect_url


def build_database(path, *, include_email, nullable):
    engine = create_engine(f"sqlite:///{path}")
    metadata = MetaData()
    Table(
        "accounts",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String(50), nullable=False),
        Column("status", String(20), nullable=nullable),
        *([Column("email", String(120), nullable=nullable)] if include_email else []),
        UniqueConstraint("name", name="uq_accounts_name"),
    )
    Table(
        "jobs",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("account_id", Integer, ForeignKey("accounts.id")),
    )
    metadata.create_all(engine)
    engine.dispose()


def test_reflection_and_diff_report_added_column_and_nullability(tmp_path):
    source_path = tmp_path / "source.db"
    target_path = tmp_path / "target.db"
    build_database(source_path, include_email=False, nullable=True)
    build_database(target_path, include_email=True, nullable=False)

    source = reflect_url(f"sqlite:///{source_path}", label="source")
    target = reflect_url(f"sqlite:///{target_path}", label="target")
    findings = compare_snapshots(source, target)
    assert {"kind": "column_only_in_target", "table": "accounts", "column": "email"} in findings
    assert {"kind": "column_changed", "table": "accounts", "column": "status", "field": "nullable", "source": True, "target": False} in findings
    assert source["tables"]["jobs"]["foreign_keys"] == target["tables"]["jobs"]["foreign_keys"]
    assert sorted(target["tables"]) == ["accounts", "jobs"]


def test_reflection_error_does_not_include_connection_url():
    secret_url = "postgresql+psycopg://private-user:private-password@127.0.0.1:1/private-db"
    try:
        reflect_url(secret_url, label="source")
    except Exception as exc:
        message = str(exc)
    else:
        raise AssertionError("connection should fail")
    assert "private-password" not in message
    assert "private-user" not in message
    assert "127.0.0.1" not in message
