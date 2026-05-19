"""Build the aretil DuckDB database.

Applies the schema, loads the committed fixtures, and resolves party name
variants into canonical entities (Splink). Later issues add embeddings (#6)
and the SQL-macro tool layer (#7).

Run:  python scripts/build_db.py
"""

from __future__ import annotations

import json
from pathlib import Path

import duckdb

from embed_matters import embed_matters
from init_db import DEFAULT_DB_PATH, STORAGE_VERSION, apply_schema
from resolve_entities import resolve_parties

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = REPO_ROOT / "data" / "fixtures"

# Fixture tables in foreign-key-safe load order: a table's FK targets load first.
LOAD_ORDER = [
    "clients",
    "timekeepers",
    "tags",
    "matters",
    "matter_timekeepers",
    "parties",
    "matter_tags",
]

# Columns whose fixture value is a JSON object bound for a VARIANT column.
VARIANT_COLUMNS = {"matters": "attributes"}


def _load_fixture(name: str) -> list[dict]:
    return json.loads((FIXTURES_DIR / f"{name}.json").read_text())


def _insert_rows(
    con: duckdb.DuckDBPyConnection, table: str, rows: list[dict],
) -> None:
    """Insert fixture rows into a table, routing JSON objects into VARIANT."""
    if not rows:
        return
    columns = list(rows[0].keys())
    variant_col = VARIANT_COLUMNS.get(table)
    # A VARIANT column needs the value parsed as JSON first; a plain string
    # cast would store the object as an opaque scalar.
    placeholders = ", ".join(
        "CAST(CAST(? AS JSON) AS VARIANT)" if col == variant_col else "?"
        for col in columns
    )
    sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
    params = [
        [json.dumps(row[col]) if col == variant_col else row[col] for col in columns]
        for row in rows
    ]
    con.executemany(sql, params)


def build_database(db_path: Path = DEFAULT_DB_PATH, *, embed: bool = True) -> Path:
    """Create a fresh DuckDB database, apply the schema, and load all fixtures.

    Also resolves party entities and, when ``embed`` is true, embeds the
    matters for semantic search. Any existing file at ``db_path`` is replaced;
    foreign-key constraints are enforced on insert, so a successful build is
    referentially sound.
    """
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.unlink(missing_ok=True)
    con = duckdb.connect(
        str(db_path),
        config={"storage_compatibility_version": STORAGE_VERSION},
    )
    try:
        apply_schema(con)
        for table in LOAD_ORDER:
            rows = _load_fixture(table)
            _insert_rows(con, table, rows)
            print(f"  loaded {table}: {len(rows)} rows")
        resolve_parties(con)
        if embed:
            embed_matters(con)
    finally:
        con.close()
    return db_path


if __name__ == "__main__":
    built = build_database()
    print(f"Built {built}")
