from __future__ import annotations

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import make_url


class SchemaError(RuntimeError):
    """Safe-to-display configuration or reflection error."""


def validate_url(url: str) -> None:
    try:
        parsed = make_url(url)
        supported = {"sqlite", "postgresql", "postgresql+psycopg", "mysql", "mysql+pymysql", "mariadb+pymysql"}
        if parsed.drivername not in supported:
            raise ValueError
    except Exception:
        raise SchemaError("database URL is invalid or uses an unsupported driver") from None


def _safe_type(column_type, dialect) -> str:
    try:
        rendered = column_type.compile(dialect=dialect)
    except Exception:
        rendered = type(column_type).__name__
    return " ".join(str(rendered).upper().split())


def reflect_url(url: str, *, schema: str | None = None, label: str = "database") -> dict:
    validate_url(url)
    engine = None
    try:
        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as connection:
            inspector = inspect(connection)
            actual_schema = schema
            if actual_schema is None and inspector.default_schema_name != "main":
                actual_schema = inspector.default_schema_name

            tables = {}
            for table_name in sorted(inspector.get_table_names(schema=actual_schema)):
                columns = []
                for item in inspector.get_columns(table_name, schema=actual_schema):
                    computed = item.get("computed")
                    columns.append(
                        {
                            "name": item["name"],
                            "type": _safe_type(item["type"], connection.dialect),
                            "nullable": bool(item.get("nullable", True)),
                            "has_default": item.get("default") is not None or computed is not None,
                        }
                    )

                primary_key = inspector.get_pk_constraint(table_name, schema=actual_schema) or {}
                foreign_keys = []
                for fk in inspector.get_foreign_keys(table_name, schema=actual_schema):
                    foreign_keys.append(
                        {
                            "columns": list(fk.get("constrained_columns") or []),
                            "referred_schema": fk.get("referred_schema"),
                            "referred_table": fk.get("referred_table"),
                            "referred_columns": list(fk.get("referred_columns") or []),
                        }
                    )
                unique_constraints = []
                for constraint in inspector.get_unique_constraints(table_name, schema=actual_schema):
                    unique_constraints.append(
                        {
                            "columns": list(constraint.get("column_names") or []),
                            "name": constraint.get("name"),
                        }
                    )
                indexes = []
                for index in inspector.get_indexes(table_name, schema=actual_schema):
                    indexes.append(
                        {
                            "columns": list(index.get("column_names") or []),
                            "name": index.get("name"),
                            "unique": bool(index.get("unique", False)),
                        }
                    )
                tables[table_name] = {
                    "columns": {column["name"]: column for column in columns},
                    "primary_key": list(primary_key.get("constrained_columns") or []),
                    "foreign_keys": sorted(foreign_keys, key=lambda item: repr(item)),
                    "unique_constraints": sorted(unique_constraints, key=lambda item: repr(item)),
                    "indexes": sorted(indexes, key=lambda item: repr(item)),
                }
            return {"schema": actual_schema, "tables": tables}
    except SchemaError:
        raise
    except Exception as exc:
        # Driver messages can contain connection URLs; expose only the failure class.
        raise SchemaError(f"{label} schema reflection failed ({type(exc).__name__})") from None
    finally:
        if engine is not None:
            engine.dispose()
