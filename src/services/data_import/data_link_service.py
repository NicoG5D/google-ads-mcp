"""Data link service implementation using Google Ads SDK."""

from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastmcp import Context, FastMCP
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.v20.enums.types.data_link_status import DataLinkStatusEnum
from google.ads.googleads.v20.resources.types.data_link import (
    DataLink,
    YoutubeVideoIdentifier,
)
from google.ads.googleads.v20.services.services.data_link_service import (
    DataLinkServiceClient,
)
from google.ads.googleads.v20.services.services.google_ads_service import (
    GoogleAdsServiceClient,
)
from google.ads.googleads.v20.services.types.data_link_service import (
    CreateDataLinkRequest,
    CreateDataLinkResponse,
    RemoveDataLinkRequest,
    RemoveDataLinkResponse,
    UpdateDataLinkRequest,
    UpdateDataLinkResponse,
)

from src.sdk_client import get_sdk_client
from src.utils import (
    format_ads_error,
    format_customer_id,
    get_logger,
    resolve_enum,
    serialize_proto_message,
)

logger = get_logger(__name__)


class DataLinkService:
    """Data link service for connecting Google Ads to external data (YouTube videos)."""

    def __init__(self) -> None:
        self._client: Optional[DataLinkServiceClient] = None

    @property
    def client(self) -> DataLinkServiceClient:
        if self._client is None:
            sdk_client = get_sdk_client()
            self._client = sdk_client.client.get_service(
                "DataLinkService", version="v20"
            )
        assert self._client is not None
        return self._client

    async def create_youtube_video_data_link(
        self,
        ctx: Context,
        customer_id: str,
        video_id: str,
        channel_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a data link to a YouTube video.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            video_id: The 11-character YouTube video ID
                (e.g. "jV1vkHv4zq8" from youtube.com/watch?v=jV1vkHv4zq8)
            channel_id: Optional YouTube channel ID (e.g. "UCK8sQmJBp8GCxrOtXWBpyEA")

        Returns:
            Created data link details
        """
        try:
            customer_id = format_customer_id(customer_id)

            youtube_video = YoutubeVideoIdentifier()
            youtube_video.video_id = video_id
            if channel_id:
                youtube_video.channel_id = channel_id

            data_link = DataLink()
            data_link.youtube_video = youtube_video

            request = CreateDataLinkRequest()
            request.customer_id = customer_id
            request.data_link = data_link

            response: CreateDataLinkResponse = self.client.create_data_link(
                request=request
            )

            await ctx.log(
                level="info",
                message=f"Created YouTube video data link for video {video_id}",
            )
            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to create data link: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def update_data_link(
        self,
        ctx: Context,
        customer_id: str,
        resource_name: str,
        status: str,
    ) -> Dict[str, Any]:
        """Update a data link's status.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            resource_name: The data link resource name
            status: New status — ENABLED, DISABLED, or REVOKED

        Returns:
            Updated data link details
        """
        try:
            customer_id = format_customer_id(customer_id)

            request = UpdateDataLinkRequest()
            request.customer_id = customer_id
            request.resource_name = resource_name
            request.data_link_status = resolve_enum(
                DataLinkStatusEnum.DataLinkStatus, status, "status"
            )

            response: UpdateDataLinkResponse = self.client.update_data_link(
                request=request
            )

            await ctx.log(
                level="info",
                message=f"Updated data link {resource_name} to status {status}",
            )
            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to update data link: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def remove_data_link(
        self,
        ctx: Context,
        customer_id: str,
        resource_name: str,
    ) -> Dict[str, Any]:
        """Remove a data link.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            resource_name: The data link resource name to remove

        Returns:
            Removal result
        """
        try:
            customer_id = format_customer_id(customer_id)

            request = RemoveDataLinkRequest()
            request.customer_id = customer_id
            request.resource_name = resource_name

            response: RemoveDataLinkResponse = self.client.remove_data_link(
                request=request
            )

            await ctx.log(
                level="info",
                message=f"Removed data link {resource_name}",
            )
            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to remove data link: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def list_data_links(
        self,
        ctx: Context,
        customer_id: str,
        status_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List data links for a customer.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            status_filter: Optional status filter (ENABLED, DISABLED, REVOKED, etc.)

        Returns:
            List of data links
        """
        try:
            customer_id = format_customer_id(customer_id)

            sdk_client = get_sdk_client()
            google_ads_service: GoogleAdsServiceClient = sdk_client.client.get_service(
                "GoogleAdsService"
            )

            query = """
                SELECT
                    data_link.resource_name,
                    data_link.data_link_id,
                    data_link.product_link_id,
                    data_link.type,
                    data_link.status,
                    data_link.youtube_video.video_id,
                    data_link.youtube_video.channel_id
                FROM data_link
            """

            if status_filter:
                query += f" WHERE data_link.status = '{status_filter}'"

            query += " ORDER BY data_link.data_link_id"

            response = google_ads_service.search(customer_id=customer_id, query=query)
            results = [serialize_proto_message(row) for row in response]

            await ctx.log(
                level="info",
                message=f"Found {len(results)} data links",
            )
            return results

        except Exception as e:
            error_msg = f"Failed to list data links: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e


def create_data_link_tools(
    service: DataLinkService,
) -> List[Callable[..., Awaitable[Any]]]:
    """Create MCP tool functions for the data link service."""
    tools = []

    async def create_youtube_video_data_link(
        ctx: Context,
        customer_id: str,
        video_id: str,
        channel_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a data link connecting a Google Ads account to a YouTube video.

        Data links allow Google Ads to access YouTube video metrics for
        reporting and attribution. The link must be approved by the video owner.

        Args:
            customer_id: The customer ID
            video_id: The 11-character YouTube video ID
                (from the URL: youtube.com/watch?v=<video_id>)
            channel_id: Optional channel ID (starts with "UC")

        Returns:
            Created data link with resource_name and status (starts as REQUESTED,
            requires approval from the YouTube channel owner)
        """
        return await service.create_youtube_video_data_link(
            ctx=ctx,
            customer_id=customer_id,
            video_id=video_id,
            channel_id=channel_id,
        )

    async def update_data_link(
        ctx: Context,
        customer_id: str,
        resource_name: str,
        status: str,
    ) -> Dict[str, Any]:
        """Update a data link's status.

        Args:
            customer_id: The customer ID
            resource_name: The data link resource name
            status: New status:
                - ENABLED: Active link
                - DISABLED: Temporarily disabled
                - REVOKED: Permanently revoked

        Returns:
            Updated data link details
        """
        return await service.update_data_link(
            ctx=ctx,
            customer_id=customer_id,
            resource_name=resource_name,
            status=status,
        )

    async def remove_data_link(
        ctx: Context,
        customer_id: str,
        resource_name: str,
    ) -> Dict[str, Any]:
        """Remove a data link.

        Args:
            customer_id: The customer ID
            resource_name: The data link resource name to remove

        Returns:
            Removal result
        """
        return await service.remove_data_link(
            ctx=ctx,
            customer_id=customer_id,
            resource_name=resource_name,
        )

    async def list_data_links(
        ctx: Context,
        customer_id: str,
        status_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List data links for a customer.

        Args:
            customer_id: The customer ID
            status_filter: Optional filter by status:
                REQUESTED, PENDING_APPROVAL, ENABLED, DISABLED, REVOKED, REJECTED

        Returns:
            List of data links with type, status, and video/channel details
        """
        return await service.list_data_links(
            ctx=ctx,
            customer_id=customer_id,
            status_filter=status_filter,
        )

    tools.extend(
        [
            create_youtube_video_data_link,
            update_data_link,
            remove_data_link,
            list_data_links,
        ]
    )
    return tools


def register_data_link_tools(mcp: FastMCP[Any]) -> DataLinkService:
    """Register data link tools with the MCP server."""
    service = DataLinkService()
    for tool in create_data_link_tools(service):
        mcp.tool(tool)
    return service
