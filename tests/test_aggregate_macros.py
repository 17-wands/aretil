"""Aggregation-macro tests — client history, market terms, pitch context."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

from build_db import build_database
from embed_matters import embed_query
from init_db import STORAGE_VERSION, apply_schema
from install_macros import install_macros


@pytest.fixture(scope="module")
def built_db(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return build_database(tmp_path_factory.mktemp("db") / "aretil.duckdb", embed=True)


def test_get_client_history_happy_path(built_db: Path) -> None:
    """A real client returns its matters with via_subsidiary = FALSE."""
    con = duckdb.connect(str(built_db), read_only=True)
    try:
        # Pick a client that actually has matters.
        name = con.execute(
            "SELECT c.name FROM clients c "
            "JOIN matters m USING (client_id) "
            "GROUP BY c.name ORDER BY count(*) DESC LIMIT 1"
        ).fetchone()[0]
        rows = con.execute(
            "SELECT * FROM get_client_history(?)", [name]
        ).fetchall()
        assert rows, f"expected matters for {name}"
        # Columns: matter_id, matter_name, client_id, client_name,
        # via_subsidiary, practice_area, deal_type, jurisdiction, deal_value,
        # year, firm_role, description
        assert all(row[3] == name for row in rows)
        assert all(row[4] is False for row in rows), (
            "no fixture client has a subsidiary; via_subsidiary should be FALSE"
        )
        years = [row[9] for row in rows]
        assert years == sorted(years, reverse=True)
    finally:
        con.close()


def test_get_client_history_subsidiary_path(tmp_path: Path) -> None:
    """A subsidiary's matters surface under the parent with via_subsidiary = TRUE.

    The committed fixtures have no parent/subsidiary links, so the subsidiary
    branch of `get_client_history` is exercised against a controlled in-memory
    DuckDB seeded with a minimal parent + subsidiary + matters set.
    """
    db_path = tmp_path / "subsidiary.duckdb"
    con = duckdb.connect(
        str(db_path),
        config={"storage_compatibility_version": STORAGE_VERSION},
    )
    try:
        apply_schema(con)
        con.execute(
            "INSERT INTO clients (client_id, name, industry, parent_client_id) "
            "VALUES (?, ?, ?, ?)",
            ["C-PARENT", "Parent Co.", "Technology", None],
        )
        con.execute(
            "INSERT INTO clients (client_id, name, industry, parent_client_id) "
            "VALUES (?, ?, ?, ?)",
            ["C-SUB", "Sub Co.", "Technology", "C-PARENT"],
        )
        con.executemany(
            "INSERT INTO matters (matter_id, name, client_id, practice_area, "
            "deal_type, jurisdiction, deal_value, year, firm_role, description) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                ["M-PARENT-1", "Parent Matter", "C-PARENT", "Tech M&A",
                 "Merger", "DE", 100_000_000, 2025, "Lead", "Parent deal"],
                ["M-SUB-1", "Sub Matter", "C-SUB", "Tech M&A",
                 "Merger", "DE", 50_000_000, 2024, "Lead", "Sub deal"],
            ],
        )
        install_macros(con)

        rows = con.execute(
            "SELECT matter_id, client_name, via_subsidiary "
            "FROM get_client_history(?) ORDER BY matter_id",
            ["Parent Co."],
        ).fetchall()
        # Both the parent's matter and the subsidiary's matter come back.
        by_id = {row[0]: row for row in rows}
        assert set(by_id) == {"M-PARENT-1", "M-SUB-1"}
        assert by_id["M-PARENT-1"][1] == "Parent Co."
        assert by_id["M-PARENT-1"][2] is False
        assert by_id["M-SUB-1"][1] == "Sub Co."
        assert by_id["M-SUB-1"][2] is True
    finally:
        con.close()


def test_get_market_terms_monotonic_quantiles(built_db: Path) -> None:
    """Quantile stats are monotonic and the year range is well-formed."""
    con = duckdb.connect(str(built_db), read_only=True)
    try:
        row = con.execute(
            "SELECT matter_count, earliest_year, latest_year, "
            "       min_value, p25_value, median_value, p75_value, max_value "
            "FROM get_market_terms(?)",
            ["Merger"],
        ).fetchone()
        (matter_count, earliest, latest,
         min_v, p25, median, p75, max_v) = row
        assert matter_count > 0
        assert earliest <= latest
        assert min_v <= p25 <= median <= p75 <= max_v
    finally:
        con.close()


def test_assemble_pitch_context_nested_shape(built_db: Path) -> None:
    """matters and timekeepers are lists of structs; market_terms is a struct."""
    con = duckdb.connect(str(built_db), read_only=True)
    try:
        emb = embed_query("healthcare pharmaceutical company merger")
        row = con.execute(
            "SELECT matters, timekeepers, market_terms "
            "FROM assemble_pitch_context(?, q_deal_type := ?, "
            "                            matter_limit := 5, timekeeper_limit := 5)",
            [emb, "Merger"],
        ).fetchone()
        matters, timekeepers, market_terms = row

        assert isinstance(matters, list) and matters
        assert len(matters) <= 5
        assert isinstance(matters[0], dict)
        # similarity is descending across the list.
        sims = [m["similarity"] for m in matters]
        assert sims == sorted(sims, reverse=True)
        # Healthcare query should be Healthcare-dominated.
        practice_areas = [m["practice_area"] for m in matters]
        assert practice_areas.count("Healthcare M&A") >= 3, (
            f"top-5 practice areas: {practice_areas}"
        )

        assert isinstance(timekeepers, list) and timekeepers
        assert len(timekeepers) <= 5
        assert isinstance(timekeepers[0], dict)
        relevances = [tk["top_relevance"] for tk in timekeepers]
        assert relevances == sorted(relevances, reverse=True)

        assert isinstance(market_terms, dict)
        assert market_terms["matter_count"] > 0
    finally:
        con.close()


def test_assemble_pitch_context_null_deal_type_drops_market_terms(
    built_db: Path,
) -> None:
    """With no q_deal_type, market_terms is NULL but matters/timekeepers fill."""
    con = duckdb.connect(str(built_db), read_only=True)
    try:
        emb = embed_query("healthcare pharmaceutical company merger")
        row = con.execute(
            "SELECT matters, timekeepers, market_terms "
            "FROM assemble_pitch_context(?, matter_limit := 3, "
            "                            timekeeper_limit := 3)",
            [emb],
        ).fetchone()
        matters, timekeepers, market_terms = row
        assert market_terms is None
        assert isinstance(matters, list) and matters
        assert isinstance(timekeepers, list) and timekeepers
    finally:
        con.close()
