"""Campaign Group service implementation with full v20 type safety."""

from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastmcp import Context, FastMCP
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.v20.enums.types.campaign_group_status import (
    CampaignGroupStatusEnum,
)
from google.ads.googleads.v20.enums.types.response_content_type import (
    ResponseContentTypeEnum,
)
from google.ads.googleads.v20.resources.types.campaign_group import CampaignGroup
from google.ads.googleads.v20.services.services.campaign_group_service import (
    CampaignGroupServiceClient,
)
from google.ads.googleads.v20.services.types.campaign_group_service import (
    CampaignGroupOperation,
    MutateCampaignGroupsRequest,
    MutateCampaignGroupsResponse,
)
from google.protobuf import field_mask_pb2

from src.sdk_client import get_sdk_client
from src.utils import (
    format_ads_error,
    format_customer_id,
    get_logger,
    resolve_enum,
    serialize_proto_message,
)

logger = get_logger(__name__)


class CampaignGroupService:
    """Service for managing campaign groups in Google Ads.

    Campaign groups allow you to organize campaigns into logical groups
    for easier management and reporting.
    """

    def __init__(self) -> None:
        self._client: Optional[CampaignGroupServiceClient] = None

    @property
    def client(self) -> CampaignGroupServiceClient:
        if self._client is None:
            sdk_client = get_sdk_client()
            self._client = sdk_client.client.get_service(
                "CampaignGroupService", version="v20"
            )
        assert self._client is not None
        return self._client

    async def create_campaign_group(
        self,
        ctx: Context,
        customer_id: str,
        name: str,
        status: CampaignGroupStatusEnum.CampaignGroupStatus = CampaignGroupStatusEnum.CampaignGroupStatus.ENABLED,
        partial_failure: bool = False,
        validate_only: bool = False,
        response_content_type: ResponseContentTypeEnum.ResponseContentType = ResponseContentTypeEnum.ResponseContentType.MUTABLE_RESOURCE,
    ) -> Dict[str, Any]:
        """Create a new campaign group.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            name: The name of the campaign group
            status: The status of the campaign group (defaults to ENABLED)
            partial_failure: If true, valid operations succeed even if others fail
            validate_only: If true, only validates without executing
            response_content_type: What to return in response

        Returns:
            Created campaign group details
        """
        try:
            customer_id = format_customer_id(customer_id)

            campaign_group = CampaignGroup()
            campaign_group.name = name
            campaign_group.status = status

            operation = CampaignGroupOperation()
            operation.create = campaign_group

            request = MutateCampaignGroupsRequest()
            request.customer_id = customer_id
            request.operations = [operation]
            request.partial_failure = partial_failure
            request.validate_only = validate_only
            request.response_content_type = response_content_type

            response: MutateCampaignGroupsResponse = (
                self.client.mutate_campaign_groups(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Created campaign group '{name}' for customer {customer_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to create campaign group: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def update_campaign_group(
        self,
        ctx: Context,
        customer_id: str,
        campaign_group_id: str,
        name: Optional[str] = None,
        status: Optional[CampaignGroupStatusEnum.CampaignGroupStatus] = None,
        partial_failure: bool = False,
        validate_only: bool = False,
        response_content_type: ResponseContentTypeEnum.ResponseContentType = ResponseContentTypeEnum.ResponseContentType.MUTABLE_RESOURCE,
    ) -> Dict[str, Any]:
        """Update an existing campaign group.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            campaign_group_id: The campaign group ID to update
            name: New name for the campaign group
            status: New status for the campaign group
            partial_failure: If true, valid operations succeed even if others fail
            validate_only: If true, only validates without executing
            response_content_type: What to return in response

        Returns:
            Updated campaign group details
        """
        try:
            customer_id = format_customer_id(customer_id)
            resource_name = f"customers/{customer_id}/campaignGroups/{campaign_group_id}"

            campaign_group = CampaignGroup()
            campaign_group.resource_name = resource_name

            update_fields = []
            if name is not None:
                campaign_group.name = name
                update_fields.append("name")
            if status is not None:
                campaign_group.status = status
                update_fields.append("status")

            operation = CampaignGroupOperation()
            operation.update = campaign_group
            operation.update_mask = field_mask_pb2.FieldMask(paths=update_fields)

            request = MutateCampaignGroupsRequest()
            request.customer_id = customer_id
            request.operations = [operation]
            request.partial_failure = partial_failure
            request.validate_only = validate_only
            request.response_content_type = response_content_type

            response: MutateCampaignGroupsResponse = (
                self.client.mutate_campaign_groups(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Updated campaign group {campaign_group_id} for customer {customer_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to update campaign group: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def remove_campaign_group(
        self,
        ctx: Context,
        customer_id: str,
        campaign_group_id: str,
        partial_failure: bool = False,
        validate_only: bool = False,
    ) -> Dict[str, Any]:
        """Remove a campaign group.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            campaign_group_id: The campaign group ID to remove
            partial_failure: If true, valid operations succeed even if others fail
            validate_only: If true, only validates without executing

        Returns:
            Removal result details
        """
        try:
            customer_id = format_customer_id(customer_id)
            resource_name = f"customers/{customer_id}/campaignGroups/{campaign_group_id}"

            operation = CampaignGroupOperation()
            operation.remove = resource_name

            request = MutateCampaignGroupsRequest()
            request.customer_id = customer_id
            request.operations = [operation]
            request.partial_failure = partial_failure
            request.validate_only = validate_only

            response = self.client.mutate_campaign_groups(request=request)

            await ctx.log(
                level="info",
                message=f"Removed campaign group {campaign_group_id} for customer {customer_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to remove campaign group: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e


def create_campaign_group_tools(
    service: CampaignGroupService,
) -> List[Callable[..., Awaitable[Any]]]:
    """Create tool functions for the campaign group service."""
    tools = []

    async def create_campaign_group(
        ctx: Context,
        customer_id: str,
        name: str,
        status: str = "ENABLED",
        partial_failure: bool = False,
        validate_only: bool = False,
    ) -> Dict[str, Any]:
        """Create a new campaign group to organize campaigns.

        Campaign groups allow you to bundle related campaigns for shared
        management, reporting, and performance targets.

        Args:
            customer_id: The customer ID
            name: The name of the campaign group
            status: Group status - ENABLED or REMOVED (default: ENABLED)
            partial_failure: If true, valid operations succeed even if others fail
            validate_only: If true, only validates without executing

        Returns:
            Created campaign group details

        Example:
            result = await create_campaign_group(
                customer_id="1234567890",
                name="Brand Awareness Campaigns"
            )
        """
        status_enum = resolve_enum(
            CampaignGroupStatusEnum.CampaignGroupStatus,
            status,
            "status",
        )
        return await service.create_campaign_group(
            ctx=ctx,
            customer_id=customer_id,
            name=name,
            status=status_enum,
            partial_failure=partial_failure,
            validate_only=validate_only,
        )

    async def update_campaign_group(
        ctx: Context,
        customer_id: str,
        campaign_group_id: str,
        name: Optional[str] = None,
        status: Optional[str] = None,
        partial_failure: bool = False,
        validate_only: bool = False,
    ) -> Dict[str, Any]:
        """Update an existing campaign group.

        Args:
            customer_id: The customer ID
            campaign_group_id: The campaign group ID to update
            name: New name for the campaign group
            status: New status - ENABLED or REMOVED
            partial_failure: If true, valid operations succeed even if others fail
            validate_only: If true, only validates without executing

        Returns:
            Updated campaign group details

        Example:
            result = await update_campaign_group(
                customer_id="1234567890",
                campaign_group_id="111222333",
                name="Performance Max Campaigns"
            )
        """
        status_enum: Optional[CampaignGroupStatusEnum.CampaignGroupStatus] = None
        if status is not None:
            status_enum = resolve_enum(
                CampaignGroupStatusEnum.CampaignGroupStatus,
                status,
                "status",
            )
        return await service.update_campaign_group(
            ctx=ctx,
            customer_id=customer_id,
            campaign_group_id=campaign_group_id,
            name=name,
            status=status_enum,
            partial_failure=partial_failure,
            validate_only=validate_only,
        )

    async def remove_campaign_group(
        ctx: Context,
        customer_id: str,
        campaign_group_id: str,
        partial_failure: bool = False,
        validate_only: bool = False,
    ) -> Dict[str, Any]:
        """Remove a campaign group.

        Args:
            customer_id: The customer ID
            campaign_group_id: The campaign group ID to remove
            partial_failure: If true, valid operations succeed even if others fail
            validate_only: If true, only validates without executing

        Returns:
            Removal result details

        Example:
            result = await remove_campaign_group(
                customer_id="1234567890",
                campaign_group_id="111222333"
            )
        """
        return await service.remove_campaign_group(
            ctx=ctx,
            customer_id=customer_id,
            campaign_group_id=campaign_group_id,
            partial_failure=partial_failure,
            validate_only=validate_only,
        )

    tools.extend([create_campaign_group, update_campaign_group, remove_campaign_group])
    return tools


def register_campaign_group_tools(
    mcp: FastMCP[Any],
) -> CampaignGroupService:
    """Register campaign group tools with the MCP server.

    Returns the service instance for testing purposes.
    """
    service = CampaignGroupService()
    tools = create_campaign_group_tools(service)

    for tool in tools:
        mcp.tool(tool)

    return service
