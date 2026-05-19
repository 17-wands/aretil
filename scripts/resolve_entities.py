"""Entity resolution — cluster party name variants into canonical entities.

Counsel, advisor, and counterparty names appear in many forms ("Latham &
Watkins LLP", "Latham", "L&W"). Each name is normalised into match keys, and
Splink deterministic linkage clusters the variants; the clusters populate the
resolved_parties and party_resolution tables.

Linkage is deterministic (not probabilistic / EM-trained): the dataset is small
and the variant relationships are exact on a derived key, so deterministic
rules are reliable and explainable here.

Abbreviation and token-substring matching is restricted to firm names (counsel
and advisors). Counterparty companies have no variant forms in this dataset, so
they resolve on the exact normalised name only — which avoids false merges from
shared initials (e.g. the abbreviation "S&C" against a company that also
initials to "sc").
"""

from __future__ import annotations

import logging
import re

import duckdb
import pandas as pd
import splink.comparison_library as cl
from splink import DuckDBAPI, Linker, SettingsCreator, block_on

logging.getLogger("splink").setLevel(logging.ERROR)

# Entity-type words stripped during normalisation — they carry no identity.
_SUFFIX_WORDS = frozenset({
    "llp", "llc", "lp", "ltd", "plc", "inc", "incorporated", "corp",
    "corporation", "co", "company", "group", "holdings", "the", "and",
})

# Firm names (counsel, advisors) carry variant forms — short names and
# abbreviations — so firm pairs also match on a compact key, a token-substring
# relationship, or an abbreviation against another firm's initials.
_FIRM_MATCH_RULE = (
    "l.kind = 'firm' AND r.kind = 'firm' AND ("
    "l.name_compact = r.name_compact "
    "OR (' ' || l.name_key || ' ') LIKE ('% ' || r.name_key || ' %') "
    "OR (' ' || r.name_key || ' ') LIKE ('% ' || l.name_key || ' %') "
    "OR l.abbrev = r.initials "
    "OR r.abbrev = l.initials)"
)


def _normalize(raw_name: str) -> str:
    """Lowercase, drop entity-type words and punctuation, collapse whitespace."""
    text = raw_name.lower().replace("&", " ")
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    return " ".join(t for t in text.split() if t and t not in _SUFFIX_WORDS)


def _features(raw_name: str, kind: str) -> dict:
    name_key = _normalize(raw_name)
    tokens = name_key.split()
    is_abbrev = len(tokens) >= 2 and all(len(token) == 1 for token in tokens)
    return {
        "raw_name": raw_name,
        "kind": kind,
        "name_key": name_key,
        "name_compact": name_key.replace(" ", ""),
        # abbrev: set only when the name itself is an abbreviation ("L&W" -> "lw").
        "abbrev": "".join(tokens) if is_abbrev else None,
        # initials: initials of any multi-word name, matched against abbrev.
        "initials": "".join(t[0] for t in tokens) if len(tokens) >= 2 else None,
    }


def _cluster_names(named_kinds: list[tuple[str, str]]) -> dict[str, int]:
    """Cluster (raw_name, kind) records into entities; return raw_name -> id."""
    frame = pd.DataFrame(
        [
            {"unique_id": i, **_features(name, kind)}
            for i, (name, kind) in enumerate(named_kinds)
        ]
    )
    settings = SettingsCreator(
        link_type="dedupe_only",
        comparisons=[cl.ExactMatch("name_key")],
        blocking_rules_to_generate_predictions=[
            block_on("name_key"),
            _FIRM_MATCH_RULE,
        ],
    )
    linker = Linker(frame, settings, db_api=DuckDBAPI())
    links = linker.inference.deterministic_link()
    clusters = linker.clustering.cluster_pairwise_predictions_at_threshold(links)
    cluster_df = clusters.as_pandas_dataframe()
    id_to_name = dict(zip(frame["unique_id"], frame["raw_name"]))
    result = {
        id_to_name[uid]: int(cid)
        for uid, cid in zip(cluster_df["unique_id"], cluster_df["cluster_id"])
    }
    # Defensive: any record absent from the clustering output is its own entity.
    next_id = max(result.values()) + 1 if result else 0
    for name, _ in named_kinds:
        if name not in result:
            result[name] = next_id
            next_id += 1
    return result


def resolve_parties(con: duckdb.DuckDBPyConnection) -> None:
    """Populate resolved_parties and party_resolution from the parties table."""
    parties = con.execute(
        "SELECT party_id, raw_name, party_type FROM parties"
    ).fetchall()
    # Counsel and advisors are firms (variant-rich); counterparties are companies.
    kinds: dict[str, str] = {}
    for _, raw_name, party_type in parties:
        if party_type in ("opposing_counsel", "advisor"):
            kinds[raw_name] = "firm"
        else:
            kinds.setdefault(raw_name, "company")
    named_kinds = sorted(kinds.items())
    name_to_cluster = _cluster_names(named_kinds)

    members: dict[int, list[str]] = {}
    for name, cluster in name_to_cluster.items():
        members.setdefault(cluster, []).append(name)

    # Canonical name per cluster: the longest member (the most complete form).
    cluster_to_id: dict[int, str] = {}
    resolved_rows: list[tuple[str, str]] = []
    for index, cluster in enumerate(sorted(members), start=1):
        canonical_id = f"RP{index:04d}"
        cluster_to_id[cluster] = canonical_id
        resolved_rows.append((canonical_id, max(members[cluster], key=len)))

    con.executemany(
        "INSERT INTO resolved_parties (canonical_party_id, canonical_name) "
        "VALUES (?, ?)",
        resolved_rows,
    )
    con.executemany(
        "INSERT INTO party_resolution (party_id, canonical_party_id) VALUES (?, ?)",
        [
            (party_id, cluster_to_id[name_to_cluster[raw_name]])
            for party_id, raw_name, _ in parties
        ],
    )
    print(f"  resolved {len(parties)} parties into {len(resolved_rows)} entities")
