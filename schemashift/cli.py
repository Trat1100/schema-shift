from __future__ import annotations

import argparse
import json
import os
import re
import sys

from .diff import compare_snapshots
from .reflect import SchemaError, reflect_url
from .report import render_json, render_text

ENV_NAME = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")


def _read_url(name: str, label: str) -> str:
    if not ENV_NAME.fullmatch(name):
        raise SchemaError(f"{label} environment variable name is invalid")
    value = os.environ.get(name, "")
    if not value:
        raise SchemaError(f"{label} environment variable {name} is not set")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="schemashift", description="Compare relational database schemas without reading rows.")
    commands = parser.add_subparsers(dest="command", required=True)
    compare = commands.add_parser("compare", help="reflect and compare two databases")
    compare.add_argument("--source-env", default="SCHEMASHIFT_SOURCE_URL")
    compare.add_argument("--target-env", default="SCHEMASHIFT_TARGET_URL")
    compare.add_argument("--schema")
    compare.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    try:
        source_url = _read_url(args.source_env, "source")
        target_url = _read_url(args.target_env, "target")
        source = reflect_url(source_url, schema=args.schema, label="source")
        target = reflect_url(target_url, schema=args.schema, label="target")
        findings = compare_snapshots(source, target)
        output = render_json(source, target, findings) if args.format == "json" else render_text(source, target, findings)
        print(output)
        return 1 if findings else 0
    except SchemaError as exc:
        print(f"schemashift: {exc}", file=sys.stderr)
        return 2
    except (OSError, ValueError) as exc:
        print(f"schemashift: comparison failed ({type(exc).__name__})", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
