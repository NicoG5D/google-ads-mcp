"""Tests for UserInterestService."""

from typing import Any
from unittest.mock import Mock, patch

import pytest
from fastmcp import Context
from google.ads.googleads.v20.enums.types.user_interest_taxonomy_type import (
    UserInterestTaxonomyTypeEnum,
)
from google.ads.googleads.v20.services.services.google_ads_service import (
    GoogleAdsServiceClient,
)

from src.services.audiences.user_interest_service import (
    UserInterestService,
    create_user_interest_tools,
    register_user_interest_tools,
)


def _make_taxonomy_mock(taxonomy_type: Any) -> Mock:
    """Wrap a real enum value in a Mock so .name is writable."""
    m = Mock()
    m.name = taxonomy_type.name
    return m


def _make_ui_row(
    user_interest_id: int,
    name: str,
    taxonomy_type: Any,
    parent: str = "",
    launched_to_all: bool = True,
) -> Mock:
    """Build a mock GoogleAdsRow containing a user_interest."""
    row = Mock()
    ui = Mock()
    ui.user_interest_id = user_interest_id
    ui.name = name
    ui.taxonomy_type = _make_taxonomy_mock(taxonomy_type)
    ui.user_interest_parent = parent
    ui.launched_to_all = launched_to_all
    ui.resource_name = f"customers/1234567890/userInterests/{user_interest_id}"
    row.user_interest = ui
    return row


_AFFINITY = UserInterestTaxonomyTypeEnum.UserInterestTaxonomyType.AFFINITY
_IN_MARKET = UserInterestTaxonomyTypeEnum.UserInterestTaxonomyType.IN_MARKET


@pytest.fixture
def mock_gaql_service() -> Mock:
    return Mock(spec=GoogleAdsServiceClient)


@pytest.fixture
def user_interest_service(
    mock_sdk_client: Any, mock_gaql_service: Mock
) -> UserInterestService:
    mock_sdk_client.client.get_service.return_value = mock_gaql_service
    with patch(
        "src.services.audiences.user_interest_service.get_sdk_client",
        return_value=mock_sdk_client,
    ):
        return UserInterestService()


# ---------------------------------------------------------------------------
# list_user_interests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_user_interests_affinity(
    user_interest_service: UserInterestService,
    mock_sdk_client: Any,
    mock_gaql_service: Mock,
    mock_ctx: Context,
) -> None:
    """list_user_interests returns correctly mapped rows for AFFINITY type."""
    rows = [
        _make_ui_row(100, "Sports & Fitness", _AFFINITY),
        _make_ui_row(101, "Sports Fans > Football/Soccer", _AFFINITY),
    ]
    mock_gaql_service.search.return_value = rows

    with patch(
        "src.services.audiences.user_interest_service.get_sdk_client",
        return_value=mock_sdk_client,
    ):
        results = await user_interest_service.list_user_interests(
            ctx=mock_ctx,
            customer_id="1234567890",
            taxonomy_type="AFFINITY",
        )

    assert len(results) == 2
    assert results[0]["user_interest_id"] == "100"
    assert results[0]["name"] == "Sports & Fitness"
    assert results[1]["name"] == "Sports Fans > Football/Soccer"

    # Verify the GAQL query contained the right filters
    call_args = mock_gaql_service.search.call_args
    query: str = call_args.kwargs["query"]
    assert "taxonomy_type = 'AFFINITY'" in query
    assert "launched_to_all = TRUE" in query


@pytest.mark.asyncio
async def test_list_user_interests_in_market(
    user_interest_service: UserInterestService,
    mock_sdk_client: Any,
    mock_gaql_service: Mock,
    mock_ctx: Context,
) -> None:
    """list_user_interests sends the correct taxonomy_type filter for IN_MARKET."""
    mock_gaql_service.search.return_value = []

    with patch(
        "src.services.audiences.user_interest_service.get_sdk_client",
        return_value=mock_sdk_client,
    ):
        await user_interest_service.list_user_interests(
            ctx=mock_ctx,
            customer_id="1234567890",
            taxonomy_type="IN_MARKET",
            launched_to_all_only=False,
        )

    query: str = mock_gaql_service.search.call_args.kwargs["query"]
    assert "taxonomy_type = 'IN_MARKET'" in query
    assert "launched_to_all = TRUE" not in query


@pytest.mark.asyncio
async def test_list_user_interests_respects_limit(
    user_interest_service: UserInterestService,
    mock_sdk_client: Any,
    mock_gaql_service: Mock,
    mock_ctx: Context,
) -> None:
    mock_gaql_service.search.return_value = []

    with patch(
        "src.services.audiences.user_interest_service.get_sdk_client",
        return_value=mock_sdk_client,
    ):
        await user_interest_service.list_user_interests(
            ctx=mock_ctx,
            customer_id="1234567890",
            taxonomy_type="AFFINITY",
            limit=50,
        )

    query: str = mock_gaql_service.search.call_args.kwargs["query"]
    assert "LIMIT 50" in query


@pytest.mark.asyncio
async def test_list_user_interests_error(
    user_interest_service: UserInterestService,
    mock_sdk_client: Any,
    mock_gaql_service: Mock,
    mock_ctx: Context,
) -> None:
    mock_gaql_service.search.side_effect = Exception("API error")

    with patch(
        "src.services.audiences.user_interest_service.get_sdk_client",
        return_value=mock_sdk_client,
    ):
        with pytest.raises(Exception, match="Failed to list user interests"):
            await user_interest_service.list_user_interests(
                ctx=mock_ctx,
                customer_id="1234567890",
                taxonomy_type="AFFINITY",
            )


# ---------------------------------------------------------------------------
# search_user_interests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_user_interests_keyword_only(
    user_interest_service: UserInterestService,
    mock_sdk_client: Any,
    mock_gaql_service: Mock,
    mock_ctx: Context,
) -> None:
    """search_user_interests with no taxonomy_type searches across all types."""
    row = _make_ui_row(101, "Sports Fans > Football/Soccer", _AFFINITY)
    mock_gaql_service.search.return_value = [row]

    with patch(
        "src.services.audiences.user_interest_service.get_sdk_client",
        return_value=mock_sdk_client,
    ):
        results = await user_interest_service.search_user_interests(
            ctx=mock_ctx,
            customer_id="1234567890",
            keyword="football",
        )

    assert len(results) == 1
    assert results[0]["name"] == "Sports Fans > Football/Soccer"

    query: str = mock_gaql_service.search.call_args.kwargs["query"]
    assert "name LIKE '%football%'" in query
    assert "taxonomy_type = '" not in query


@pytest.mark.asyncio
async def test_search_user_interests_with_taxonomy_filter(
    user_interest_service: UserInterestService,
    mock_sdk_client: Any,
    mock_gaql_service: Mock,
    mock_ctx: Context,
) -> None:
    mock_gaql_service.search.return_value = []

    with patch(
        "src.services.audiences.user_interest_service.get_sdk_client",
        return_value=mock_sdk_client,
    ):
        await user_interest_service.search_user_interests(
            ctx=mock_ctx,
            customer_id="1234567890",
            keyword="sport",
            taxonomy_type="AFFINITY",
        )

    query: str = mock_gaql_service.search.call_args.kwargs["query"]
    assert "name LIKE '%sport%'" in query
    assert "taxonomy_type = 'AFFINITY'" in query


@pytest.mark.asyncio
async def test_search_user_interests_empty_result(
    user_interest_service: UserInterestService,
    mock_sdk_client: Any,
    mock_gaql_service: Mock,
    mock_ctx: Context,
) -> None:
    mock_gaql_service.search.return_value = []

    with patch(
        "src.services.audiences.user_interest_service.get_sdk_client",
        return_value=mock_sdk_client,
    ):
        results = await user_interest_service.search_user_interests(
            ctx=mock_ctx,
            customer_id="1234567890",
            keyword="zzznomatch",
        )

    assert results == []


@pytest.mark.asyncio
async def test_search_user_interests_error(
    user_interest_service: UserInterestService,
    mock_sdk_client: Any,
    mock_gaql_service: Mock,
    mock_ctx: Context,
) -> None:
    mock_gaql_service.search.side_effect = Exception("connection refused")

    with patch(
        "src.services.audiences.user_interest_service.get_sdk_client",
        return_value=mock_sdk_client,
    ):
        with pytest.raises(Exception, match="Failed to search user interests"):
            await user_interest_service.search_user_interests(
                ctx=mock_ctx,
                customer_id="1234567890",
                keyword="sport",
            )


# ---------------------------------------------------------------------------
# get_user_interest
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_user_interest_found(
    user_interest_service: UserInterestService,
    mock_sdk_client: Any,
    mock_gaql_service: Mock,
    mock_ctx: Context,
) -> None:
    row = _make_ui_row(101, "Sports Fans > Football/Soccer", _AFFINITY)
    mock_gaql_service.search.return_value = [row]

    with patch(
        "src.services.audiences.user_interest_service.get_sdk_client",
        return_value=mock_sdk_client,
    ):
        result = await user_interest_service.get_user_interest(
            ctx=mock_ctx,
            customer_id="1234567890",
            user_interest_id="101",
        )

    assert result["user_interest_id"] == "101"
    assert result["name"] == "Sports Fans > Football/Soccer"

    query: str = mock_gaql_service.search.call_args.kwargs["query"]
    assert "user_interest_id = 101" in query


@pytest.mark.asyncio
async def test_get_user_interest_not_found(
    user_interest_service: UserInterestService,
    mock_sdk_client: Any,
    mock_gaql_service: Mock,
    mock_ctx: Context,
) -> None:
    mock_gaql_service.search.return_value = []

    with patch(
        "src.services.audiences.user_interest_service.get_sdk_client",
        return_value=mock_sdk_client,
    ):
        with pytest.raises(Exception, match="not found"):
            await user_interest_service.get_user_interest(
                ctx=mock_ctx,
                customer_id="1234567890",
                user_interest_id="9999",
            )


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------


def test_register_user_interest_tools(mock_sdk_client: Any) -> None:
    """register_user_interest_tools registers all 3 tools with the MCP server."""
    from fastmcp import FastMCP

    mcp = FastMCP(name="test")
    with patch(
        "src.services.audiences.user_interest_service.get_sdk_client",
        return_value=mock_sdk_client,
    ):
        service = register_user_interest_tools(mcp)

    assert isinstance(service, UserInterestService)


def test_create_user_interest_tools_returns_three_callables(
    mock_sdk_client: Any,
) -> None:
    """create_user_interest_tools returns exactly 3 tool functions."""
    with patch(
        "src.services.audiences.user_interest_service.get_sdk_client",
        return_value=mock_sdk_client,
    ):
        service = UserInterestService()
        tools = create_user_interest_tools(service)

    assert len(tools) == 3
    names = {t.__name__ for t in tools}
    assert names == {
        "list_user_interests",
        "search_user_interests",
        "get_user_interest",
    }
