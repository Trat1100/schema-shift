# SchemaShift

SchemaShift compares two relational database schemas and reports structural drift without reading application rows or changing either database.

## What it compares

- Tables and columns.
- Database-reported column types and nullability.
- Presence of a server-side default, without printing its literal value.
- Primary keys, foreign keys, unique constraints, and indexes.
- Text or JSON reports with automation-friendly exit codes.

SchemaShift uses SQLAlchemy's database reflection. SQLite is built in; PostgreSQL and MySQL/MariaDB drivers are included. Comparison is most useful between instances of the same database engine. Backend-specific type spellings can differ across engines.

## Install

Requires Python 3.11 or later.

~~~powershell
python -m pip install .
~~~

## Usage

Set URLs in the shell so passwords do not appear in shell history or process arguments:

~~~powershell
$env:SCHEMASHIFT_SOURCE_URL = 'sqlite:///source.db'
$env:SCHEMASHIFT_TARGET_URL = 'sqlite:///target.db'
schemashift compare --format text
schemashift compare --format json
~~~

For PostgreSQL or MySQL, set the matching SQLAlchemy URL in the same environment variables. Use a dedicated read-only database account. The tool reports only environment variable names when configuration is missing; it never prints a supplied URL or password.

Exit codes: 0 means no detected drift, 1 means schemas differ, and 2 means configuration or connection failed.

For development, install the pinned test tools with `python -m pip install --require-hashes -r requirements-dev.lock`, then install the checkout with `python -m pip install --no-deps --no-build-isolation -e .`.

## Safety and limits

- Uses SQLAlchemy's schema inspector and does not issue DDL or read table rows.
- Uses database catalog metadata. A read-only account is still recommended.
- Reports default presence but never the default expression or literal value.
- Does not compare stored data, triggers, procedures, permissions, or every vendor-specific schema feature.
- Schema metadata can itself be sensitive; review output before sharing it.
- Use the same engine family on both sides for the most useful type comparison.

## Development

~~~powershell
python -m pytest -q
~~~

Tests use temporary SQLite databases and synthetic schema definitions. GitHub Actions runs on Python 3.11 and 3.12.

## Project structure

- schemashift/reflect.py — read-only database reflection and normalization.
- schemashift/diff.py — deterministic structural drift findings.
- schemashift/report.py — text and JSON renderers.
- schemashift/cli.py — environment-based CLI.

## License

MIT. See the included LICENSE file.
