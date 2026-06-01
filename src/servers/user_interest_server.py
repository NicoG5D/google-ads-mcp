"""User interest server for browsing Google's predefined audience categories."""

from fastmcp import FastMCP

from src.services.audiences.user_interest_service import register_user_interest_tools

user_interest_server = FastMCP(
    name="user_interest",
    instructions="""This server provides read-only access to Google's predefined audience categories
    (affinity audiences and in-market audiences).

    These are audiences maintained by Google, not user-created ones.

    Available tools:
    - list_user_interests: List all audiences of a given taxonomy type (AFFINITY, IN_MARKET, etc.)
    - search_user_interests: Search audiences by keyword (e.g. "football", "travel", "gaming")
    - get_user_interest: Retrieve a specific audience by its numeric ID

    Typical workflow for Display campaign targeting:
    1. Call search_user_interests with a keyword and taxonomy_type="AFFINITY"
    2. Note the user_interest_id of the relevant audience(s)
    3. Use those IDs via ad_group_criterion tools to apply the targeting

    Taxonomy types:
    - AFFINITY: Long-term passion-based interests (best for brand awareness)
    - IN_MARKET: Users actively researching/comparing (best for performance)
    """,
)

user_interest_service = register_user_interest_tools(user_interest_server)
