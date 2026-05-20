"""Install the SQL macros that form the canonical tool layer.

`build_db.py` calls `install_macros()` after the fixtures are loaded and
entities resolved. The macros are stored in the DuckDB catalog and persist
with the database file; `CREATE OR REPLACE` makes the install idempotent.
"""

from __future__ import annotations

from pathlib import Path

import duckdb

REPO_ROOT = Path(__file__).resolve().parent.parent
MACROS_PATH = REPO_ROOT / "macros" / "tools.sql"


def install_macros(con: duckdb.DuckDBPyConnection) -> None:
    """Install (or replace) every macro in macros/tools.sql."""
    statements = [s for s in MACROS_PATH.read_text().split(";") if s.strip()]
    for statement in statements:
        con.execute(statement)
    print(f"  installed {len(statements)} macros from "
          f"{MACROS_PATH.relative_to(REPO_ROOT)}")
