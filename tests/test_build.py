"""Build-pipeline tests — fixtures load into the schema with integrity intact."""

from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pytest

from build_db import LOAD_ORDER, build_database

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "data" / "fixtures"


@pytest.fixture(scope="module")
def built_db(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return build_database(tmp_path_factory.mktemp("db") / "aretil.duckdb", embed=False)


def test_row_counts_match_fixtures(built_db: Path) -> None:
    con = duckdb.connect(str(built_db), read_only=True)
    try:
        for table in LOAD_ORDER:
            expected = len(json.loads((FIXTURES_DIR / f"{table}.json").read_text()))
            actual = con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            assert actual == expected, f"{table}: loaded {actual}, expected {expected}"
    finally:
        con.close()


def test_referential_integrity(built_db: Path) -> None:
    # (child table, foreign key, parent table, primary key)
    checks = [
        ("matters", "client_id", "clients", "client_id"),
        ("matter_timekeepers", "matter_id", "matters", "matter_id"),
        ("matter_timekeepers", "timekeeper_id", "timekeepers", "timekeeper_id"),
        ("parties", "matter_id", "matters", "matter_id"),
        ("matter_tags", "matter_id", "matters", "matter_id"),
        ("matter_tags", "tag_id", "tags", "tag_id"),
    ]
    con = duckdb.connect(str(built_db), read_only=True)
    try:
        for child, fk, parent, pk in checks:
            orphans = con.execute(
                f"SELECT count(*) FROM {child} c "
                f"LEFT JOIN {parent} p ON c.{fk} = p.{pk} "
                f"WHERE p.{pk} IS NULL"
            ).fetchone()[0]
            assert orphans == 0, f"{child}.{fk}: {orphans} orphan row(s)"
    finally:
        con.close()


def test_variant_attributes_loaded(built_db: Path) -> None:
    con = duckdb.connect(str(built_db), read_only=True)
    try:
        # attributes is a structured VARIANT — a known field is extractable.
        total = con.execute("SELECT count(*) FROM matters").fetchone()[0]
        with_form = con.execute(
            "SELECT count(*) FROM matters WHERE attributes.edgar_form IS NOT NULL"
        ).fetchone()[0]
        assert with_form == total
    finally:
        con.close()
