"""Tests for DataLinkService."""

from typing import Any
from unittest.mock import Mock, patch

import pytest
from fastmcp import Context
from google.ads.googleads.v20.services.services.data_link_service import (
    DataLinkServiceClient,
)
from google.ads.googleads.v20.services.services.google_ads_service import (
    GoogleAdsServiceClient,
)
from google.ads.googleads.v20.services.types.data_link_service import (
    CreateDataLinkResponse,
    RemoveDataLinkResponse,
    UpdateDataLinkResponse,
)

from src.services.data_import.data_link_service import (
    DataLinkService,
    create_data_link_tools,
    register_data_link_tools,
)


@pytest.fixture
def mock_dl_client() -> Mock:
    return Mock(spec=DataLinkServiceClient)


@pytest.fixture
def data_link_service(mock_sdk_client: Any, mock_dl_client: Mock) -> DataLinkService:
    mock_sdk_client.client.get_service.return_value = mock_dl_client
    with patch(
        "src.services.data_import.data_link_service.get_sdk_client",
        return_value=mock_sdk_client,
    ):
        service = DataLinkService()
        _ = service.client
        return service


# ---------------------------------------------------------------------------
# create_youtube_video_data_link
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_youtube_video_data_link(
    data_link_service: DataLinkService,
    mock_sdk_client: Any,
    mock_dl_client: Mock,
    mock_ctx: Context,
) -> None:
    """Test creating a YouTube video data link."""
    mock_dl_client.create_data_link.return_value = Mock(spec=CreateDataLinkResponse)
    expected = {"data_link": {"resource_name": "customers/123/datalinks/1~2"}}

    with (
        patch(
            "src.services.data_import.data_link_service.get_sdk_client",
            return_value=mock_sdk_client,
        ),
        patch(
            "src.services.data_import.data_link_service.serialize_proto_message",
            return_value=expected,
        ),
    ):
        result = await data_link_service.create_youtube_video_data_link(
            ctx=mock_ctx,
            customer_id="1234567890",
            video_id="jV1vkHv4zq8",
            channel_id="UCK8sQmJBp8GCxrOtXWBpyEA",
        )

    assert result == expected
    mock_dl_client.create_data_link.assert_called_once()
    req = mock_dl_client.create_data_link.call_args.kwargs["request"]
    assert req.customer_id == "1234567890"
    assert req.data_link.youtube_video.video_id == "jV1vkHv4zq8"
    assert req.data_link.youtube_video.channel_id == "UCK8sQmJBp8GCxrOtXWBpyEA"


@pytest.mark.asyncio
async def test_create_youtube_video_data_link_without_channel(
    data_link_service: DataLinkService,
    mock_sdk_client: Any,
    mock_dl_client: Mock,
    mock_ctx: Context,
) -> None:
    """Test creating a YouTube video data link without channel_id."""
    mock_dl_client.create_data_link.return_value = Mock(spec=CreateDataLinkResponse)

    with (
        patch(
            "src.services.data_import.data_link_service.get_sdk_client",
            return_value=mock_sdk_client,
        ),
        patch(
            "src.services.data_import.data_link_service.serialize_proto_message",
            return_value={},
        ),
    ):
        await data_link_service.create_youtube_video_data_link(
            ctx=mock_ctx,
            customer_id="1234567890",
            video_id="jV1vkHv4zq8",
        )

    req = mock_dl_client.create_data_link.call_args.kwargs["request"]
    assert req.data_link.youtube_video.video_id == "jV1vkHv4zq8"
    # channel_id should not be set (empty string is the proto default)
    assert req.data_link.youtube_video.channel_id == ""


# ---------------------------------------------------------------------------
# update_data_link
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_data_link(
    data_link_service: DataLinkService,
    mock_sdk_client: Any,
    mock_dl_client: Mock,
    mock_ctx: Context,
) -> None:
    """Test updating a data link status."""
    mock_dl_client.update_data_link.return_value = Mock(spec=UpdateDataLinkResponse)
    resource_name = "customers/1234567890/datalinks/1~2"

    with (
        patch(
            "src.services.data_import.data_link_service.get_sdk_client",
            return_value=mock_sdk_client,
        ),
        patch(
            "src.services.data_import.data_link_service.serialize_proto_message",
            return_value={},
        ),
    ):
        await data_link_service.update_data_link(
            ctx=mock_ctx,
            customer_id="1234567890",
            resource_name=resource_name,
            status="DISABLED",
        )

    req = mock_dl_client.update_data_link.call_args.kwargs["request"]
    assert req.customer_id == "1234567890"
    assert req.resource_name == resource_name


# ---------------------------------------------------------------------------
# remove_data_link
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_remove_data_link(
    data_link_service: DataLinkService,
    mock_sdk_client: Any,
    mock_dl_client: Mock,
    mock_ctx: Context,
) -> None:
    """Test removing a data link."""
    mock_dl_client.remove_data_link.return_value = Mock(spec=RemoveDataLinkResponse)
    resource_name = "customers/1234567890/datalinks/1~2"

    with (
        patch(
            "src.services.data_import.data_link_service.get_sdk_client",
            return_value=mock_sdk_client,
        ),
        patch(
            "src.services.data_import.data_link_service.serialize_proto_message",
            return_value={},
        ),
    ):
        await data_link_service.remove_data_link(
            ctx=mock_ctx,
            customer_id="1234567890",
            resource_name=resource_name,
        )

    req = mock_dl_client.remove_data_link.call_args.kwargs["request"]
    assert req.customer_id == "1234567890"
    assert req.resource_name == resource_name


# ---------------------------------------------------------------------------
# list_data_links
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_data_links(
    data_link_service: DataLinkService,
    mock_sdk_client: Any,
    mock_dl_client: Mock,
    mock_ctx: Context,
) -> None:
    """Test listing data links."""
    mock_gaql = Mock(spec=GoogleAdsServiceClient)
    mock_gaql.search.return_value = [Mock(), Mock()]
    mock_sdk_client.client.get_service.return_value = mock_gaql

    with (
        patch(
            "src.services.data_import.data_link_service.get_sdk_client",
            return_value=mock_sdk_client,
        ),
        patch(
            "src.services.data_import.data_link_service.serialize_proto_message",
            return_value={"data_link": {}},
        ),
    ):
        results = await data_link_service.list_data_links(
            ctx=mock_ctx,
            customer_id="1234567890",
        )

    assert len(results) == 2
    query: str = mock_gaql.search.call_args.kwargs["query"]
    assert "data_link" in query
    assert "WHERE" not in query


@pytest.mark.asyncio
async def test_list_data_links_with_status_filter(
    data_link_service: DataLinkService,
    mock_sdk_client: Any,
    mock_dl_client: Mock,
    mock_ctx: Context,
) -> None:
    """Test listing data links filtered by status."""
    mock_gaql = Mock(spec=GoogleAdsServiceClient)
    mock_gaql.search.return_value = []
    mock_sdk_client.client.get_service.return_value = mock_gaql

    with (
        patch(
            "src.services.data_import.data_link_service.get_sdk_client",
            return_value=mock_sdk_client,
        ),
        patch(
            "src.services.data_import.data_link_service.serialize_proto_message",
            return_value={},
        ),
    ):
        await data_link_service.list_data_links(
            ctx=mock_ctx,
            customer_id="1234567890",
            status_filter="ENABLED",
        )

    query: str = mock_gaql.search.call_args.kwargs["query"]
    assert "data_link.status = 'ENABLED'" in query


# ---------------------------------------------------------------------------
# error handling
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_error_handling(
    data_link_service: DataLinkService,
    mock_sdk_client: Any,
    mock_dl_client: Mock,
    mock_ctx: Context,
) -> None:
    mock_dl_client.create_data_link.side_effect = Exception("network error")

    with patch(
        "src.services.data_import.data_link_service.get_sdk_client",
        return_value=mock_sdk_client,
    ):
        with pytest.raises(Exception, match="Failed to create data link"):
            await data_link_service.create_youtube_video_data_link(
                ctx=mock_ctx,
                customer_id="1234567890",
                video_id="abc",
            )


# ---------------------------------------------------------------------------
# tool registration
# ---------------------------------------------------------------------------


def test_tool_names(mock_sdk_client: Any) -> None:
    with patch(
        "src.services.data_import.data_link_service.get_sdk_client",
        return_value=mock_sdk_client,
    ):
        tools = create_data_link_tools(DataLinkService())

    names = {t.__name__ for t in tools}
    assert names == {
        "create_youtube_video_data_link",
        "update_data_link",
        "remove_data_link",
        "list_data_links",
    }


def test_register_creates_service(mock_sdk_client: Any) -> None:
    from fastmcp import FastMCP

    mcp = FastMCP(name="test")
    with patch(
        "src.services.data_import.data_link_service.get_sdk_client",
        return_value=mock_sdk_client,
    ):
        service = register_data_link_tools(mcp)

    assert isinstance(service, DataLinkService)
