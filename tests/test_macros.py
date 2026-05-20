"""SQL-macro tool-layer tests — search, timekeeper ranking, history."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

from build_db import build_database
from embed_matters import embed_query


@pytest.fixture(scope="module")
def built_db(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return build_database(tmp_path_factory.mktemp("db") / "aretil.duckdb", embed=True)


def test_search_matters_returns_ranked_rows(built_db: Path) -> None:
    con = duckdb.connect(str(built_db), read_only=True)
    try:
        rows = con.execute(
            "SELECT * FROM search_matters(?, result_limit := 5)",
            [embed_query("healthcare pharmaceutical company merger")],
        ).fetchall()
        assert len(rows) == 5
        # similarity is the last column; results are descending.
        sims = [row[-1] for row in rows]
        assert all(0.0 <= s <= 1.0 for s in sims)
        assert sims == sorted(sims, reverse=True)
    finally:
        con.close()


def test_search_matters_filters_by_practice_area(built_db: Path) -> None:
    con = duckdb.connect(str(built_db), read_only=True)
    try:
        rows = con.execute(
            "SELECT practice_area "
            "FROM search_matters(?, practice_area := ?, result_limit := 50)",
            [embed_query("merger acquisition"), "Healthcare M&A"],
        ).fetchall()
        assert rows
        assert {row[0] for row in rows} == {"Healthcare M&A"}
    finally:
        con.close()


def test_search_matters_counsel_variant_resolution(built_db: Path) -> None:
    """A counsel filter on any Latham variant must return the same matters."""
    con = duckdb.connect(str(built_db), read_only=True)
    try:
        emb = embed_query("M&A")
        result_sets = []
        for variant in ("L&W", "Latham", "Latham & Watkins LLP"):
            rows = con.execute(
                "SELECT matter_id "
                "FROM search_matters(?, counsel := ?, result_limit := 200)",
                [emb, variant],
            ).fetchall()
            result_sets.append({row[0] for row in rows})
        assert result_sets[0], "no matters returned for Latham counsel filter"
        assert all(s == result_sets[0] for s in result_sets), (
            f"Latham variants returned different matter sets: {result_sets}"
        )
    finally:
        con.close()


def test_find_relevant_timekeepers_ranked(built_db: Path) -> None:
    con = duckdb.connect(str(built_db), read_only=True)
    try:
        rows = con.execute(
            "SELECT * FROM find_relevant_timekeepers(?, result_limit := 5)",
            [embed_query("healthcare pharmaceutical merger")],
        ).fetchall()
        assert len(rows) == 5
        # top_relevance is column index 5; results sorted descending by it.
        top = [row[5] for row in rows]
        assert top == sorted(top, reverse=True)
    finally:
        con.close()


def test_get_timekeeper_history(built_db: Path) -> None:
    con = duckdb.connect(str(built_db), read_only=True)
    try:
        # Pick a timekeeper who actually appears on a matter.
        name = con.execute(
            "SELECT t.name FROM timekeepers t "
            "JOIN matter_timekeepers mt USING (timekeeper_id) "
            "GROUP BY t.name LIMIT 1"
        ).fetchone()[0]
        rows = con.execute(
            "SELECT * FROM get_timekeeper_history(?)", [name]
        ).fetchall()
        assert rows
        # cols: timekeeper_id, name, matter_id, matter_name, practice_area,
        # deal_type, year, deal_value, role_on_matter, description
        roles = {row[8] for row in rows}
        assert roles <= {"Lead", "Supporting", "Associate"}
    finally:
        con.close()
