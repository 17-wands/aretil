"""Fixture tests — the EDGAR-seeded dataset matches the schema and PRD §7."""

from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pytest

from init_db import apply_schema

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "data" / "fixtures"

# fixture file (without .json) -> schema table
FIXTURE_TABLES = {
    "clients": "clients",
    "matters": "matters",
    "timekeepers": "timekeepers",
    "matter_timekeepers": "matter_timekeepers",
    "parties": "parties",
    "tags": "tags",
    "matter_tags": "matter_tags",
}


@pytest.fixture(scope="module")
def fixtures() -> dict[str, list[dict]]:
    return {
        name: json.loads((FIXTURES_DIR / f"{name}.json").read_text())
        for name in FIXTURE_TABLES
    }


@pytest.fixture(scope="module")
def schema_columns() -> dict[str, set[str]]:
    con = duckdb.connect(":memory:")
    try:
        apply_schema(con)
        return {
            table: {row[0] for row in con.execute(f"DESCRIBE {table}").fetchall()}
            for table in FIXTURE_TABLES.values()
        }
    finally:
        con.close()


def test_all_fixture_files_present(fixtures: dict[str, list[dict]]) -> None:
    for name, rows in fixtures.items():
        assert isinstance(rows, list) and rows, f"{name}.json is missing or empty"


def test_matter_count_in_range(fixtures: dict[str, list[dict]]) -> None:
    assert 50 <= len(fixtures["matters"]) <= 100


def test_practice_areas_have_depth(fixtures: dict[str, list[dict]]) -> None:
    areas = {m["practice_area"] for m in fixtures["matters"]}
    assert len(areas) >= 2


def test_counsel_name_variants(fixtures: dict[str, list[dict]]) -> None:
    # PRD §7 D.6: at least one counsel firm appears under three name variants.
    latham = {"Latham & Watkins LLP", "Latham & Watkins", "Latham", "L&W"}
    raw_names = {
        p["raw_name"]
        for p in fixtures["parties"]
        if p["party_type"] == "opposing_counsel"
    }
    assert len(latham & raw_names) >= 3


def test_fixture_shape_matches_schema(
    fixtures: dict[str, list[dict]], schema_columns: dict[str, set[str]],
) -> None:
    for name, table in FIXTURE_TABLES.items():
        columns = schema_columns[table]
        for record in fixtures[name]:
            assert set(record) == columns, f"{name}.json record keys != {table} columns"


def test_referential_integrity(fixtures: dict[str, list[dict]]) -> None:
    client_ids = {c["client_id"] for c in fixtures["clients"]}
    matter_ids = {m["matter_id"] for m in fixtures["matters"]}
    timekeeper_ids = {t["timekeeper_id"] for t in fixtures["timekeepers"]}
    tag_ids = {t["tag_id"] for t in fixtures["tags"]}

    assert all(m["client_id"] in client_ids for m in fixtures["matters"])
    assert all(p["matter_id"] in matter_ids for p in fixtures["parties"])
    for row in fixtures["matter_timekeepers"]:
        assert row["matter_id"] in matter_ids
        assert row["timekeeper_id"] in timekeeper_ids
    for row in fixtures["matter_tags"]:
        assert row["matter_id"] in matter_ids
        assert row["tag_id"] in tag_ids
