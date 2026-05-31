"""Shareable Preview service implementation with full v20 type safety."""

from typing import Any, Awaitable, Callable, Dict, List, Optional, Sequence

from fastmcp import Context, FastMCP
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.v20.services.services.shareable_preview_service import (
    ShareablePreviewServiceClient,
)
from google.ads.googleads.v20.services.types.shareable_preview_service import (
    AssetGroupIdentifier,
    GenerateShareablePreviewsRequest,
    GenerateShareablePreviewsResponse,
    ShareablePreview,
)

from src.sdk_client import get_sdk_client
from src.utils import (
    format_ads_error,
    format_customer_id,
    get_logger,
    serialize_proto_message,
)

logger = get_logger(__name__)


class ShareablePreviewService:
    """Service for generating shareable previews of asset groups in Google Ads.

    Shareable previews allow advertisers to share a preview URL for asset
    groups before a campaign goes live.
    """

    def __init__(self) -> None:
        self._client: Optional[ShareablePreviewServiceClient] = None

    @property
    def client(self) -> ShareablePreviewServiceClient:
        if self._client is None:
            sdk_client = get_sdk_client()
            self._client = sdk_client.client.get_service(
                "ShareablePreviewService", version="v20"
            )
        assert self._client is not None
        return self._client

    async def generate_shareable_previews(
        self,
        ctx: Context,
        customer_id: str,
        asset_group_ids: Sequence[int],
    ) -> Dict[str, Any]:
        """Generate shareable preview URLs for asset groups.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID owning the asset groups
            asset_group_ids: List of asset group IDs to generate previews for

        Returns:
            Response containing shareable preview URLs or partial failure errors
        """
        try:
            formatted_customer_id = format_customer_id(customer_id)

            shareable_previews: List[ShareablePreview] = []
            for asset_group_id in asset_group_ids:
                identifier = AssetGroupIdentifier()
                identifier.asset_group_id = asset_group_id
                preview = ShareablePreview()
                preview.asset_group_identifier = identifier
                shareable_previews.append(preview)

            request = GenerateShareablePreviewsRequest()
            request.customer_id = formatted_customer_id
            request.shareable_previews = shareable_previews

            response: GenerateShareablePreviewsResponse = (
                self.client.generate_shareable_previews(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Generated shareable previews for customer {formatted_customer_id} "
                f"with {len(asset_group_ids)} asset group(s)",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to generate shareable previews: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e


def create_shareable_preview_tools(
    service: ShareablePreviewService,
) -> List[Callable[..., Awaitable[Any]]]:
    """Create tool functions for the shareable preview service."""
    tools = []

    async def generate_shareable_previews(
        ctx: Context,
        customer_id: str,
        asset_group_ids: List[int],
    ) -> Dict[str, Any]:
        """Generate shareable preview URLs for asset groups.

        Creates shareable preview URLs that can be shared with stakeholders
        before an asset group campaign goes live. Each preview URL expires
        after a set period.

        Args:
            customer_id: The customer ID (with or without hyphens)
            asset_group_ids: List of asset group IDs to generate previews for

        Returns:
            Response with shareable preview URLs and expiration datetimes
            for each asset group, or partial failure errors if any failed

        Example:
            result = await generate_shareable_previews(
                customer_id="1234567890",
                asset_group_ids=[111222333, 444555666]
            )
        """
        return await service.generate_shareable_previews(
            ctx=ctx,
            customer_id=customer_id,
            asset_group_ids=asset_group_ids,
        )

    tools.append(generate_shareable_previews)
    return tools


def register_shareable_preview_tools(
    mcp: FastMCP[Any],
) -> ShareablePreviewService:
    """Register shareable preview tools with the MCP server.

    Returns the service instance for testing purposes.
    """
    service = ShareablePreviewService()
    tools = create_shareable_preview_tools(service)

    for tool in tools:
        mcp.tool(tool)

    return service
