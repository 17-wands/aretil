"""Schema tests — verify the ARCHITECTURE.md §4 tables, columns, and foreign keys."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import duckdb
import pytest

from init_db import apply_schema, create_database

EXPECTED_COLUMNS = {
    "clients": {"client_id", "name", "industry", "parent_client_id"},
    "matters": {
        "matter_id", "name", "client_id", "practice_area", "deal_type",
        "jurisdiction", "deal_value", "year", "firm_role", "description",
        "attributes",
    },
    "timekeepers": {
        "timekeeper_id", "name", "title", "practice_group", "years_experience",
    },
    "matter_timekeepers": {"matter_id", "timekeeper_id", "role_on_matter"},
    "parties": {"party_id", "matter_id", "raw_name", "party_type", "side"},
    "resolved_parties": {"canonical_party_id", "canonical_name"},
    "party_resolution": {"party_id", "canonical_party_id"},
    "tags": {"tag_id", "tag_type", "value"},
    "matter_tags": {"matter_id", "tag_id"},
    "matter_embeddings": {"matter_id", "embedding"},
}

# Tables that must carry at least one foreign key (ARCHITECTURE.md §4).
FK_TABLES = {
    "clients", "matters", "matter_timekeepers", "parties",
    "party_resolution", "matter_tags", "matter_embeddings",
}


@pytest.fixture
def con() -> Iterator[duckdb.DuckDBPyConnection]:
    connection = duckdb.connect(":memory:")
    apply_schema(connection)
    yield connection
    connection.close()


def test_all_tables_exist(con: duckdb.DuckDBPyConnection) -> None:
    rows = con.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'main'"
    ).fetchall()
    tables = {row[0] for row in rows}
    assert set(EXPECTED_COLUMNS) <= tables


def test_key_columns_exist(con: duckdb.DuckDBPyConnection) -> None:
    for table, expected in EXPECTED_COLUMNS.items():
        rows = con.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'main' AND table_name = ?",
            [table],
        ).fetchall()
        actual = {row[0] for row in rows}
        assert not expected - actual, f"{table} missing: {expected - actual}"


def test_matters_attributes_is_variant(con: duckdb.DuckDBPyConnection) -> None:
    rows = con.execute("DESCRIBE matters").fetchall()
    column_types = {row[0]: row[1] for row in rows}
    assert "attributes" in column_types
    assert "VARIANT" in column_types["attributes"].upper()


def test_foreign_keys_exist(con: duckdb.DuckDBPyConnection) -> None:
    rows = con.execute(
        "SELECT DISTINCT table_name FROM duckdb_constraints() "
        "WHERE constraint_type = 'FOREIGN KEY'"
    ).fetchall()
    fk_tables = {row[0] for row in rows}
    assert not FK_TABLES - fk_tables, f"missing FKs: {FK_TABLES - fk_tables}"


def test_create_database_persists_schema(tmp_path: Path) -> None:
    db_path = create_database(tmp_path / "aretil.duckdb")
    assert db_path.exists()
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        tables = {
            row[0]
            for row in con.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'main'"
            ).fetchall()
        }
    finally:
        con.close()
    assert set(EXPECTED_COLUMNS) <= tables
