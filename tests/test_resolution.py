"""Entity-resolution tests — party name variants cluster to one canonical id."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

from build_db import build_database

LATHAM_VARIANTS = ("Latham & Watkins LLP", "Latham & Watkins", "Latham", "L&W")


@pytest.fixture(scope="module")
def built_db(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return build_database(tmp_path_factory.mktemp("db") / "aretil.duckdb", embed=False)


def test_every_party_is_resolved(built_db: Path) -> None:
    con = duckdb.connect(str(built_db), read_only=True)
    try:
        parties = con.execute("SELECT count(*) FROM parties").fetchone()[0]
        resolved = con.execute("SELECT count(*) FROM party_resolution").fetchone()[0]
        assert resolved == parties
    finally:
        con.close()


def test_latham_variants_resolve_to_one_entity(built_db: Path) -> None:
    con = duckdb.connect(str(built_db), read_only=True)
    try:
        placeholders = ", ".join("?" for _ in LATHAM_VARIANTS)
        ids = con.execute(
            "SELECT DISTINCT pr.canonical_party_id "
            "FROM parties p JOIN party_resolution pr USING (party_id) "
            f"WHERE p.raw_name IN ({placeholders})",
            list(LATHAM_VARIANTS),
        ).fetchall()
        assert len(ids) == 1, f"Latham variants split across {len(ids)} entities"
    finally:
        con.close()


def test_resolution_references_valid_entities(built_db: Path) -> None:
    con = duckdb.connect(str(built_db), read_only=True)
    try:
        orphans = con.execute(
            "SELECT count(*) FROM party_resolution pr "
            "LEFT JOIN resolved_parties rp USING (canonical_party_id) "
            "WHERE rp.canonical_party_id IS NULL"
        ).fetchone()[0]
        assert orphans == 0
        entities = con.execute("SELECT count(*) FROM resolved_parties").fetchone()[0]
        assert entities > 0
    finally:
        con.close()


def test_no_company_firm_cross_merge(built_db: Path) -> None:
    # A counterparty company and a counsel/advisor firm must never land in the
    # same canonical entity — guards against shared-initials false merges.
    con = duckdb.connect(str(built_db), read_only=True)
    try:
        mixed = con.execute(
            "SELECT pr.canonical_party_id, "
            "count(*) FILTER (WHERE p.party_type = 'counterparty') AS companies, "
            "count(*) FILTER (WHERE p.party_type IN ('opposing_counsel', 'advisor')) "
            "  AS firms "
            "FROM party_resolution pr JOIN parties p USING (party_id) "
            "GROUP BY pr.canonical_party_id "
            "HAVING companies > 0 AND firms > 0"
        ).fetchall()
        assert mixed == [], f"entities mixing company and firm parties: {mixed}"
    finally:
        con.close()
