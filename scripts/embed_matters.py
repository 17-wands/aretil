"""Matter embeddings and semantic search.

Each matter is embedded into a vector with model2vec — a pure-numpy static
embedding model (no PyTorch), so it runs anywhere. The text embedded per matter
combines the matter name, practice area, deal type, the client's real industry,
and the description, so a topical query ("healthcare M&A") ranks matters by
subject. Vectors are stored in the matter_embeddings table and searched in SQL
with DuckDB's array_cosine_similarity.
"""

from __future__ import annotations

import functools

import duckdb
from model2vec import StaticModel

MODEL_NAME = "minishlab/potion-base-8M"
EMBED_DIM = 256


@functools.lru_cache(maxsize=1)
def _model() -> StaticModel:
    return StaticModel.from_pretrained(MODEL_NAME)


def _matter_text(
    name: str,
    practice_area: str,
    deal_type: str,
    industry: str | None,
    description: str,
) -> str:
    """Compose the text embedded for a matter from its key fields."""
    parts = [name, practice_area, deal_type]
    if industry:
        parts.append(f"Industry: {industry}")
    if description:
        parts.append(description)
    return ". ".join(part for part in parts if part)


def embed_matters(con: duckdb.DuckDBPyConnection) -> None:
    """Embed every matter and populate the matter_embeddings table."""
    rows = con.execute(
        "SELECT m.matter_id, m.name, m.practice_area, m.deal_type, "
        "       c.industry, m.description "
        "FROM matters m JOIN clients c USING (client_id) "
        "ORDER BY m.matter_id"
    ).fetchall()
    texts = [_matter_text(*row[1:]) for row in rows]
    vectors = _model().encode(texts)
    con.executemany(
        "INSERT INTO matter_embeddings (matter_id, embedding) VALUES (?, ?)",
        [(row[0], vector.tolist()) for row, vector in zip(rows, vectors)],
    )
    print(f"  embedded {len(rows)} matters ({EMBED_DIM}-dim)")


def semantic_search(
    con: duckdb.DuckDBPyConnection, query: str, limit: int = 10,
) -> list[tuple[str, str, float]]:
    """Return (matter_id, name, similarity) for the matters closest to query."""
    query_vector = _model().encode([query])[0].tolist()
    return con.execute(
        "SELECT m.matter_id, m.name, "
        f"array_cosine_similarity(e.embedding, ?::FLOAT[{EMBED_DIM}]) AS similarity "
        "FROM matter_embeddings e JOIN matters m USING (matter_id) "
        "ORDER BY similarity DESC LIMIT ?",
        [query_vector, limit],
    ).fetchall()
