"""Semantic-search tests — embeddings rank matters by topic."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

from build_db import build_database
from embed_matters import semantic_search


@pytest.fixture(scope="module")
def built_db(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return build_database(tmp_path_factory.mktemp("db") / "aretil.duckdb", embed=True)


@pytest.fixture(scope="module")
def practice_area(built_db: Path) -> dict[str, str]:
    con = duckdb.connect(str(built_db), read_only=True)
    try:
        return dict(con.execute("SELECT matter_id, practice_area FROM matters").fetchall())
    finally:
        con.close()


def test_every_matter_is_embedded(built_db: Path) -> None:
    con = duckdb.connect(str(built_db), read_only=True)
    try:
        matters = con.execute("SELECT count(*) FROM matters").fetchone()[0]
        embedded = con.execute("SELECT count(*) FROM matter_embeddings").fetchone()[0]
        assert embedded == matters
    finally:
        con.close()


def test_healthcare_query_ranks_healthcare_matters(
    built_db: Path, practice_area: dict[str, str],
) -> None:
    con = duckdb.connect(str(built_db), read_only=True)
    try:
        results = semantic_search(con, "healthcare pharmaceutical company merger", 5)
        top_areas = [practice_area[matter_id] for matter_id, _, _ in results]
        assert top_areas.count("Healthcare M&A") >= 3, f"top-5 areas: {top_areas}"
    finally:
        con.close()


def test_relevant_matters_outrank_unrelated(
    built_db: Path, practice_area: dict[str, str],
) -> None:
    # A healthcare query should score healthcare matters above technology ones.
    con = duckdb.connect(str(built_db), read_only=True)
    try:
        ranked = semantic_search(con, "healthcare pharmaceutical company merger", 200)
        healthcare = [s for mid, _, s in ranked if practice_area[mid] == "Healthcare M&A"]
        technology = [s for mid, _, s in ranked if practice_area[mid] == "Technology M&A"]
        assert healthcare and technology
        assert sum(healthcare) / len(healthcare) > sum(technology) / len(technology)
    finally:
        con.close()
