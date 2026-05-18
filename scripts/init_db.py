"""Create a DuckDB database and apply the aretil schema (see ARCHITECTURE.md §4)."""

from __future__ import annotations

from pathlib import Path

import duckdb

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "schema" / "schema.sql"
DEFAULT_DB_PATH = REPO_ROOT / "data" / "aretil.duckdb"

# VARIANT columns require DuckDB storage v1.5.0+; new database files default to
# an older storage version for backward compatibility, so it is set explicitly.
STORAGE_VERSION = "v1.5.0"


def apply_schema(con: duckdb.DuckDBPyConnection) -> None:
    """Execute the aretil schema DDL against an open DuckDB connection."""
    for statement in SCHEMA_PATH.read_text().split(";"):
        if statement.strip():
            con.execute(statement)


def create_database(db_path: Path = DEFAULT_DB_PATH) -> Path:
    """Create a fresh DuckDB database with the aretil schema.

    Any existing file at ``db_path`` is replaced.
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
    finally:
        con.close()
    return db_path


if __name__ == "__main__":
    created = create_database()
    print(f"Created {created} with the aretil schema.")
