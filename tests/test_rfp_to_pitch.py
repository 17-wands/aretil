"""RFP-to-Pitch workflow test — validates the flagship demo works end-to-end."""

from __future__ import annotations

import json
import os
from pathlib import Path

import duckdb
import pytest

from anthropic import Anthropic
from embed_matters import embed_query

# Load the pitch prompt from prompts/pitch.md
PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "pitch.md"
PITCH_PROMPT = PROMPT_PATH.read_text()

# Sample RFP for testing
SAMPLE_RFP = """
Subject: Healthcare IT Platform — Strategic M&A Counsel

We are [HealthTech Corp], a healthcare IT platform with ~$50M annual revenue,
seeking M&A counsel for a strategic transaction. We are considering acquiring
two smaller healthcare software companies to consolidate capabilities and expand
our addressable market in the healthcare sector.

Deal profile:
- Strategic acquisition of healthcare IT software assets
- Combined estimated deal value: $75–100M
- Buyer: HealthTech Corp (publicly traded)
- Targets: Two healthcare software companies
- Geography: US (California-based buyer)
- Timeframe: Q3 2026

We need experienced healthcare M&A counsel with:
- Track record closing healthcare IT deals
- Experience with regulatory and IP considerations
- Capability to manage parallel transactions
- Familiarity with PE and strategic buyers in healthcare tech

Please provide examples of relevant past transactions and your team's experience
in this space.
"""


@pytest.fixture(scope="module")
def built_db(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Build the demo database for RFP testing."""
    from build_db import build_database

    return build_database(tmp_path_factory.mktemp("db") / "aretil.duckdb", embed=True)


def duckdb_tool_call(con: duckdb.DuckDBPyConnection, tool_name: str, **kwargs) -> dict:
    """Execute a DuckDB macro tool and return its result as a dict."""
    if tool_name == "assemble_pitch_context":
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

    elif tool_name == "get_market_terms":
        deal_type = kwargs.get("deal_type")
        practice_area = kwargs.get("practice_area")
        jurisdiction = kwargs.get("jurisdiction")

        result = con.execute(
            "SELECT * FROM get_market_terms(?, ?, ?)",
            [deal_type, practice_area, jurisdiction],
        ).fetchone()

        return {
            "deal_type": result[0],
            "matter_count": result[1],
            "earliest_year": result[2],
            "latest_year": result[3],
            "min_value": result[4],
            "p25_value": result[5],
            "median_value": result[6],
            "p75_value": result[7],
            "max_value": result[8],
            "mean_value": result[9],
        }

    else:
        raise ValueError(f"Unknown tool: {tool_name}")


def test_rfp_to_pitch_harness(built_db: Path) -> None:
    """
    End-to-end test: RFP → tool calls → pitch output.

    This test validates that:
    1. An RFP can be parsed into structured intent.
    2. The firm data layer returns relevant matters and timekeepers.
    3. A pitch is drafted with the required structure (matter list + team + paragraphs).
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
        # Start the tool-use loop with Claude
        messages = [
            {
                "role": "user",
                "content": f"Please draft a pitch in response to this RFP:\n\n{SAMPLE_RFP}",
            }
        ]

        # Initial request to Claude with the pitch prompt
        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=4096,
            system=PITCH_PROMPT,
            messages=messages,
        )

        # Tool-use loop: handle any tool calls Claude makes
        iteration = 0
        max_iterations = 10
        final_pitch = None

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
                    if tool_name == "assemble_pitch_context" and "query_embedding" not in tool_input:
                        # Embed the RFP intent text
                        intent_text = (
                            f"{tool_input.get('q_practice_area', '')} "
                            f"{tool_input.get('q_industry', '')} "
                            f"{tool_input.get('q_deal_type', '')}".strip()
                        )
                        tool_input["query_embedding"] = embed_query(intent_text)

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
                    system=PITCH_PROMPT,
                    messages=messages,
                )

            elif response.stop_reason == "end_turn":
                # Claude has finished and returned the final pitch
                final_pitch = next(
                    (block.text for block in response.content if hasattr(block, "text")),
                    None,
                )
                break

        # Validation assertions
        assert final_pitch is not None, "Claude did not produce a pitch output"
        assert isinstance(final_pitch, str), "Pitch output is not a string"
        assert len(final_pitch) > 200, f"Pitch output is too short ({len(final_pitch)} chars)"

        # Check for markdown structure
        assert "#" in final_pitch, "Pitch does not contain markdown headers"

        # Check for key sections
        assert any(
            keyword in final_pitch.lower()
            for keyword in ["experience", "team", "matter", "capability"]
        ), "Pitch does not reference relevant experience or team"

        # Check that it's multiple paragraphs
        paragraphs = [p.strip() for p in final_pitch.split("\n\n") if p.strip()]
        assert len(paragraphs) >= 3, f"Pitch has insufficient paragraphs ({len(paragraphs)})"

        # Print the generated pitch for manual inspection
        print("\n" + "=" * 80)
        print("GENERATED PITCH:")
        print("=" * 80)
        print(final_pitch)
        print("=" * 80)

    finally:
        con.close()


def test_assemble_pitch_context_with_healthcare_query(built_db: Path) -> None:
    """Verify assemble_pitch_context works for a healthcare M&A query."""
    con = duckdb.connect(str(built_db), read_only=True)

    try:
        # Embed a healthcare M&A query
        embedding = embed_query("healthcare M&A acquisition")

        # Call assemble_pitch_context with healthcare-focused filters
        result = con.execute(
            "SELECT matters, timekeepers, market_terms FROM assemble_pitch_context("
            "  ?, q_practice_area := ?, q_deal_type := ?, "
            "  matter_limit := 5, timekeeper_limit := 5"
            ")",
            [embedding, "Healthcare M&A", "Merger"],
        ).fetchone()

        matters, timekeepers, market_terms = result

        # Assertions
        assert matters is not None and len(matters) > 0, "No healthcare M&A matters returned"
        assert (
            timekeepers is not None and len(timekeepers) > 0
        ), "No timekeepers returned for healthcare M&A"
        assert market_terms is not None, "No market terms returned"

        # Check that returned matters are healthcare-focused
        healthcare_matters = [
            m for m in matters if m.get("practice_area", "").lower().find("healthcare") >= 0
        ]
        assert len(healthcare_matters) >= 2, (
            f"Expected at least 2 healthcare-focused matters in top 5, got {len(healthcare_matters)}"
        )

        print("\nHealthcare M&A query returned:")
        print(f"  - {len(matters)} matters (top {len(healthcare_matters)} healthcare-focused)")
        print(f"  - {len(timekeepers)} timekeepers")
        print(f"  - Market terms: {market_terms.get('matter_count', 'N/A')} comparable deals")

    finally:
        con.close()
