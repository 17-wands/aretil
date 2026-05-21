#!/usr/bin/env python
"""DuckDB MCP server for aretil — exposes macros as MCP tools to Claude Desktop.

Usage:
    python start_mcp_server.py [path/to/database.duckdb]

If no path is provided, defaults to data/aretil.duckdb in the project root.
"""

import sys
import json
import logging
from pathlib import Path
from typing import Any

import duckdb
from mcp.server import FastMCP

# Logger for debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Get the database path from command-line arg or use default
db_path = sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent / "data" / "aretil.duckdb"
db_path = Path(db_path).resolve()

# Verify the database exists
if not db_path.exists():
    logger.error(f"Database not found: {db_path}")
    sys.exit(1)

logger.info(f"Using database: {db_path}")


# Initialize FastMCP server
server = FastMCP("aretil")


def serialize_value(val: Any) -> Any:
    """Convert DuckDB-specific types to JSON-serializable Python types."""
    if val is None:
        return None
    if isinstance(val, (str, int, float, bool)):
        return val
    if isinstance(val, (list, tuple)):
        return [serialize_value(v) for v in val]
    if isinstance(val, dict):
        return {k: serialize_value(v) for k, v in val.items()}
    # For other types (Decimal, datetime, etc.), convert to string
    return str(val)


@server.tool()
def search_matters(
    query_embedding: list[float],
    practice_area: str | None = None,
    industry: str | None = None,
    deal_type: str | None = None,
    jurisdiction: str | None = None,
    min_value: float | None = None,
    max_value: float | None = None,
) -> str:
    """Search for matters by semantic similarity over descriptions, with optional structured filters."""
    con = None
    try:
        con = duckdb.connect(str(db_path), read_only=True)
        result = con.execute(
            "SELECT * FROM search_matters(?, ?, ?, ?, ?, ?, ?)",
            [query_embedding, practice_area, industry, deal_type, jurisdiction, min_value, max_value],
        ).fetchall()

        # Convert to list of dicts for JSON serialization
        return json.dumps({
            "result": [[serialize_value(v) for v in row] for row in result]
        })
    except Exception as e:
        logger.exception("Error in search_matters")
        return json.dumps({"error": str(e)})
    finally:
        if con:
            con.close()


@server.tool()
def find_relevant_timekeepers(
    matter_ids: list[str] | None = None,
    query_text: str | None = None,
) -> str:
    """Find timekeepers most relevant to a set of matters or a search query."""
    con = None
    try:
        if not matter_ids and not query_text:
            return json.dumps({"error": "Either matter_ids or query_text required"})

        con = duckdb.connect(str(db_path), read_only=True)
        result = con.execute(
            "SELECT * FROM find_relevant_timekeepers(?, ?)",
            [matter_ids, query_text],
        ).fetchall()

        return json.dumps({
            "result": [[serialize_value(v) for v in row] for row in result]
        })
    except Exception as e:
        logger.exception("Error in find_relevant_timekeepers")
        return json.dumps({"error": str(e)})
    finally:
        if con:
            con.close()


@server.tool()
def get_client_history(client_name: str) -> str:
    """Get all matters for a client, including subsidiaries."""
    con = None
    try:
        con = duckdb.connect(str(db_path), read_only=True)
        result = con.execute(
            "SELECT * FROM get_client_history(?)",
            [client_name],
        ).fetchall()

        return json.dumps({
            "result": [[serialize_value(v) for v in row] for row in result]
        })
    except Exception as e:
        logger.exception("Error in get_client_history")
        return json.dumps({"error": str(e)})
    finally:
        if con:
            con.close()


@server.tool()
def get_market_terms(
    deal_type: str,
    practice_area: str | None = None,
    jurisdiction: str | None = None,
) -> str:
    """Get aggregate statistics for comparable matters by deal type."""
    con = None
    try:
        con = duckdb.connect(str(db_path), read_only=True)
        result = con.execute(
            "SELECT * FROM get_market_terms(?, ?, ?)",
            [deal_type, practice_area, jurisdiction],
        ).fetchall()

        return json.dumps({
            "result": [[serialize_value(v) for v in row] for row in result]
        })
    except Exception as e:
        logger.exception("Error in get_market_terms")
        return json.dumps({"error": str(e)})
    finally:
        if con:
            con.close()


@server.tool()
def get_timekeeper_history(
    timekeeper_id: str | None = None,
    name: str | None = None,
) -> str:
    """Get a timekeeper's full matter history with roles."""
    con = None
    try:
        if not timekeeper_id and not name:
            return json.dumps({"error": "Either timekeeper_id or name required"})

        con = duckdb.connect(str(db_path), read_only=True)
        # Pass whichever is provided; DuckDB will handle the non-matching param
        result = con.execute(
            "SELECT * FROM get_timekeeper_history(?)",
            [timekeeper_id or name],
        ).fetchall()

        return json.dumps({
            "result": [[serialize_value(v) for v in row] for row in result]
        })
    except Exception as e:
        logger.exception("Error in get_timekeeper_history")
        return json.dumps({"error": str(e)})
    finally:
        if con:
            con.close()


@server.tool()
def assemble_pitch_context(
    query_embedding: list[float],
    q_practice_area: str | None = None,
    q_industry: str | None = None,
    q_deal_type: str | None = None,
    q_jurisdiction: str | None = None,
    q_min_value: float | None = None,
    q_max_value: float | None = None,
    matter_limit: int = 5,
    timekeeper_limit: int = 5,
) -> str:
    """One-call pitch context: relevant matters + ranked timekeepers + market terms."""
    con = None
    try:
        con = duckdb.connect(str(db_path), read_only=True)
        result = con.execute(
            "SELECT matters, timekeepers, market_terms FROM assemble_pitch_context("
            "  ?, "
            "  q_practice_area := ?, q_industry := ?, q_deal_type := ?, "
            "  q_jurisdiction := ?, q_min_value := ?, q_max_value := ?, "
            "  matter_limit := ?, timekeeper_limit := ?"
            ")",
            [
                query_embedding,
                q_practice_area,
                q_industry,
                q_deal_type,
                q_jurisdiction,
                q_min_value,
                q_max_value,
                matter_limit,
                timekeeper_limit,
            ],
        ).fetchall()

        # This macro returns a single row with nested structures
        if result:
            row = result[0]
            return json.dumps({
                "result": {
                    "matters": serialize_value(row[0]),
                    "timekeepers": serialize_value(row[1]),
                    "market_terms": serialize_value(row[2]),
                }
            })
        else:
            return json.dumps({"result": None})
    except Exception as e:
        logger.exception("Error in assemble_pitch_context")
        return json.dumps({"error": str(e)})
    finally:
        if con:
            con.close()


if __name__ == "__main__":
    server.run()
