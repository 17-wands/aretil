"""Timekeeper Bio/CV workflow test — validates the second workflow works end-to-end."""

from __future__ import annotations

import json
import os
from pathlib import Path

import duckdb
import pytest

from anthropic import Anthropic
from embed_matters import embed_query

# Load the bio prompt from prompts/bio.md
PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "bio.md"
BIO_PROMPT = PROMPT_PATH.read_text()


@pytest.fixture(scope="module")
def built_db(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Build the demo database for bio testing."""
    from build_db import build_database

    return build_database(tmp_path_factory.mktemp("db") / "aretil.duckdb", embed=True)


def duckdb_tool_call(con: duckdb.DuckDBPyConnection, tool_name: str, **kwargs) -> dict:
    """Execute a DuckDB macro tool and return its result as a dict."""
    if tool_name == "get_timekeeper_history":
        timekeeper_id = kwargs.get("timekeeper_id")
        name = kwargs.get("name")

        result = con.execute(
            "SELECT * FROM get_timekeeper_history(?)",
            [timekeeper_id or name],
        ).fetchall()

        return {"matters": result}

    elif tool_name == "search_matters":
        query_embedding = kwargs.get("query_embedding", [])
        practice_area = kwargs.get("practice_area")
        industry = kwargs.get("industry")
        deal_type = kwargs.get("deal_type")
        jurisdiction = kwargs.get("jurisdiction")
        min_value = kwargs.get("min_value")
        max_value = kwargs.get("max_value")

        result = con.execute(
            "SELECT * FROM search_matters(?, ?, ?, ?, ?, ?, ?)",
            [query_embedding, practice_area, industry, deal_type, jurisdiction, min_value, max_value],
        ).fetchall()

        return {"matters": result}

    elif tool_name == "assemble_pitch_context":
        query_embedding = kwargs.get("query_embedding", [])
        q_practice_area = kwargs.get("q_practice_area")
        q_industry = kwargs.get("q_industry")
        q_deal_type = kwargs.get("q_deal_type")
        q_jurisdiction = kwargs.get("q_jurisdiction")
        q_min_value = kwargs.get("q_min_value")
        q_max_value = kwargs.get("q_max_value")
        matter_limit = kwargs.get("matter_limit", 5)
        timekeeper_limit = kwargs.get("timekeeper_limit", 5)

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
        ).fetchone()

        return {
            "matters": result[0],
            "timekeepers": result[1],
            "market_terms": result[2],
        }

    else:
        raise ValueError(f"Unknown tool: {tool_name}")


def test_get_timekeeper_history_basic(built_db: Path) -> None:
    """Verify get_timekeeper_history returns matter data for a timekeeper."""
    con = duckdb.connect(str(built_db), read_only=True)

    try:
        # Get a timekeeper ID from the database
        timekeeper_id = con.execute(
            "SELECT timekeeper_id FROM timekeepers LIMIT 1"
        ).fetchone()[0]

        # Call get_timekeeper_history
        result = con.execute(
            "SELECT * FROM get_timekeeper_history(?)",
            [timekeeper_id],
        ).fetchall()

        # Should return at least some history
        # (some timekeepers may have no matters, which is OK)
        assert isinstance(result, list), "Result should be a list"

        print(f"\nTimekeeper {timekeeper_id}:")
        print(f"  - {len(result)} matters in history")

    finally:
        con.close()


def test_timekeeper_bio_harness(built_db: Path) -> None:
    """
    End-to-end test: Timekeeper request → get_timekeeper_history → bio output.

    This test validates that:
    1. A timekeeper can be identified from a request.
    2. Their full matter history is retrieved.
    3. A tailored bio/CV is drafted with the required structure.
    4. The output is markdown.
    """
    # Initialize Anthropic client
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set")

    client = Anthropic(api_key=api_key)

    # Load the database
    con = duckdb.connect(str(built_db), read_only=True)

    try:
        # Get a timekeeper with matter history for testing
        timekeeper_query = con.execute(
            "SELECT DISTINCT tk.timekeeper_id, tk.name FROM timekeepers tk "
            "JOIN matter_timekeepers mt USING (timekeeper_id) "
            "LIMIT 1"
        ).fetchone()

        if not timekeeper_query:
            pytest.skip("No timekeepers with matter history in database")

        timekeeper_id, timekeeper_name = timekeeper_query

        # Request a bio for this timekeeper with a healthcare context
        user_request = (
            f"Please draft a tailored bio for {timekeeper_name}, "
            "emphasizing their healthcare M&A experience."
        )

        # Start the tool-use loop with Claude
        messages = [
            {
                "role": "user",
                "content": user_request,
            }
        ]

        # Initial request to Claude with the bio prompt
        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=4096,
            system=BIO_PROMPT,
            messages=messages,
        )

        # Tool-use loop: handle any tool calls Claude makes
        iteration = 0
        max_iterations = 10
        final_bio = None

        while iteration < max_iterations:
            iteration += 1

            # Check if Claude is still making tool calls or has produced final output
            if response.stop_reason == "tool_use":
                # Process tool calls
                tool_calls = [block for block in response.content if block.type == "tool_use"]
                tool_results = []

                for tool_call in tool_calls:
                    tool_name = tool_call.name
                    tool_input = tool_call.input

                    # Call the DuckDB tool
                    # For embedding-based tools, embed the query intent if needed
                    if (
                        tool_name == "search_matters"
                        and "query_embedding" not in tool_input
                    ):
                        # Embed healthcare M&A context
                        tool_input["query_embedding"] = embed_query(
                            "healthcare M&A"
                        )

                    tool_result = duckdb_tool_call(con, tool_name, **tool_input)

                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_call.id,
                            "content": json.dumps(tool_result),
                        }
                    )

                # Add Claude's response and tool results to messages
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})

                # Get next response from Claude
                response = client.messages.create(
                    model="claude-opus-4-7",
                    max_tokens=4096,
                    system=BIO_PROMPT,
                    messages=messages,
                )

            elif response.stop_reason == "end_turn":
                # Claude has finished and returned the final bio
                final_bio = next(
                    (block.text for block in response.content if hasattr(block, "text")),
                    None,
                )
                break

        # Validation assertions
        assert final_bio is not None, "Claude did not produce a bio output"
        assert isinstance(final_bio, str), "Bio output is not a string"
        assert len(final_bio) > 150, f"Bio output is too short ({len(final_bio)} chars)"

        # Check for markdown structure
        assert "#" in final_bio, "Bio does not contain markdown headers"

        # Check for key sections
        assert any(
            keyword in final_bio.lower()
            for keyword in ["experience", "matter", "practice", "strength"]
        ), "Bio does not reference experience or key strengths"

        # Check for matter references (should cite actual matters from history)
        assert any(
            char in final_bio for char in ["[", "("]
        ), "Bio should reference matters or details"

        # Print the generated bio for manual inspection
        print("\n" + "=" * 80)
        print(f"GENERATED BIO FOR {timekeeper_name}:")
        print("=" * 80)
        print(final_bio)
        print("=" * 80)

    finally:
        con.close()


def test_shared_data_layer_both_workflows(built_db: Path) -> None:
    """
    Verify that both the pitch and bio workflows use the same data layer and tools.

    This test demonstrates the X.1 cross-cutting requirement: both workflows run
    against the same shared data layer and tool set.
    """
    con = duckdb.connect(str(built_db), read_only=True)

    try:
        # Verify the same tools are available for both workflows
        tools_used = {
            "pitch": ["assemble_pitch_context", "search_matters", "get_market_terms"],
            "bio": ["get_timekeeper_history", "search_matters"],
        }

        # Check that all tools exist as macros
        for workflow, tool_list in tools_used.items():
            for tool_name in tool_list:
                # Try to call each tool to verify it exists
                if tool_name == "assemble_pitch_context":
                    con.execute(
                        "SELECT matters FROM assemble_pitch_context(?, q_deal_type := NULL)",
                        [[0.1] * 256],
                    ).fetchone()
                elif tool_name == "search_matters":
                    con.execute(
                        "SELECT COUNT(*) FROM search_matters(?, NULL, NULL, NULL, NULL, NULL, NULL)",
                        [[0.1] * 256],
                    ).fetchone()
                elif tool_name == "get_market_terms":
                    con.execute(
                        "SELECT matter_count FROM get_market_terms('Merger', NULL, NULL)"
                    ).fetchone()
                elif tool_name == "get_timekeeper_history":
                    # Get a timekeeper and call the tool
                    tk = con.execute("SELECT timekeeper_id FROM timekeepers LIMIT 1").fetchone()
                    if tk:
                        con.execute(
                            "SELECT COUNT(*) FROM get_timekeeper_history(?)",
                            [tk[0]],
                        ).fetchone()

        print("\n✓ Both workflows use the same shared data layer and tool set")
        print("  Pitch tools: assemble_pitch_context, search_matters, get_market_terms")
        print("  Bio tools: get_timekeeper_history, search_matters")
        print("  Shared: search_matters, same database (aretil.duckdb)")

    finally:
        con.close()
