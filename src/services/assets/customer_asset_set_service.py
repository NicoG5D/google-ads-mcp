"""Customer Asset Set service implementation with full v20 type safety."""

from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastmcp import Context, FastMCP
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.v20.enums.types.response_content_type import (
    ResponseContentTypeEnum,
)
from google.ads.googleads.v20.resources.types.customer_asset_set import CustomerAssetSet
from google.ads.googleads.v20.services.services.customer_asset_set_service import (
    CustomerAssetSetServiceClient,
)
from google.ads.googleads.v20.services.types.customer_asset_set_service import (
    CustomerAssetSetOperation,
    MutateCustomerAssetSetsRequest,
    MutateCustomerAssetSetsResponse,
)

from src.sdk_client import get_sdk_client
from src.utils import (
    format_ads_error,
    resolve_customer_id,
    get_logger,
    serialize_proto_message,
)

logger = get_logger(__name__)


class CustomerAssetSetService:
    """Service for managing customer asset sets in Google Ads.

    CustomerAssetSet is the linkage between a customer and an asset set.
    """

    def __init__(self) -> None:
        self._client: Optional[CustomerAssetSetServiceClient] = None

    @property
    def client(self) -> CustomerAssetSetServiceClient:
        if self._client is None:
            sdk_client = get_sdk_client()
            self._client = sdk_client.client.get_service(
                "CustomerAssetSetService", version="v20"
            )
        assert self._client is not None
        return self._client

    async def create_customer_asset_set(
        self,
        ctx: Context,
        *,
        customer_id: Optional[str] = None,
        asset_set: str,
        partial_failure: bool = False,
        validate_only: bool = False,
        response_content_type: ResponseContentTypeEnum.ResponseContentType = ResponseContentTypeEnum.ResponseContentType.MUTABLE_RESOURCE,
    ) -> Dict[str, Any]:
        """Link an asset set to a customer.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            asset_set: The resource name of the asset set to link to the customer
            partial_failure: If true, valid operations succeed even if others fail
            validate_only: If true, only validates without executing
            response_content_type: What to return in response

        Returns:
            Created customer asset set link details
        """
        try:
            customer_id = resolve_customer_id(customer_id)
            customer_resource = f"customers/{customer_id}"

            customer_asset_set = CustomerAssetSet()
            customer_asset_set.asset_set = asset_set
            customer_asset_set.customer = customer_resource

            operation = CustomerAssetSetOperation()
            operation.create = customer_asset_set

            request = MutateCustomerAssetSetsRequest()
            request.customer_id = customer_id
            request.operations = [operation]
            request.partial_failure = partial_failure
            request.validate_only = validate_only
            request.response_content_type = response_content_type

            response: MutateCustomerAssetSetsResponse = (
                self.client.mutate_customer_asset_sets(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Linked asset set {asset_set} to customer {customer_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to create customer asset set: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def remove_customer_asset_set(
        self,
        ctx: Context,
        *,
        customer_id: Optional[str] = None,
        asset_set_id: str,
        partial_failure: bool = False,
        validate_only: bool = False,
    ) -> Dict[str, Any]:
        """Remove an asset set link from a customer.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            asset_set_id: The asset set ID to unlink from the customer
            partial_failure: If true, valid operations succeed even if others fail
            validate_only: If true, only validates without executing

        Returns:
            Removal result details
        """
        try:
            customer_id = resolve_customer_id(customer_id)
            resource_name = f"customers/{customer_id}/customerAssetSets/{asset_set_id}"

            operation = CustomerAssetSetOperation()
            operation.remove = resource_name

            request = MutateCustomerAssetSetsRequest()
            request.customer_id = customer_id
            request.operations = [operation]
            request.partial_failure = partial_failure
            request.validate_only = validate_only

            response: MutateCustomerAssetSetsResponse = (
                self.client.mutate_customer_asset_sets(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Removed asset set {asset_set_id} from customer {customer_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to remove customer asset set: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e


def create_customer_asset_set_tools(
    service: CustomerAssetSetService,
) -> List[Callable[..., Awaitable[Any]]]:
    """Create tool functions for the customer asset set service."""
    tools = []

    async def create_customer_asset_set(
        ctx: Context,
        *,
        customer_id: Optional[str] = None,
        asset_set: str,
        partial_failure: bool = False,
        validate_only: bool = False,
    ) -> Dict[str, Any]:
        """Link an asset set to a customer account.

        Creates a CustomerAssetSet which links an asset set to the customer
        account so that the asset set is available for use across campaigns.

        Args:
            customer_id: The customer ID
            asset_set: Resource name of the asset set to link
                       (e.g. customers/123/assetSets/456)
            partial_failure: If true, valid operations succeed even if others fail
            validate_only: If true, only validates without executing

        Returns:
            Created customer asset set link details

        Example:
            result = await create_customer_asset_set(
                customer_id="1234567890",
                asset_set="customers/1234567890/assetSets/111"
            )
        """
        return await service.create_customer_asset_set(
            ctx=ctx,
            customer_id=customer_id,
            asset_set=asset_set,
            partial_failure=partial_failure,
            validate_only=validate_only,
        )

    async def remove_customer_asset_set(
        ctx: Context,
        *,
        customer_id: Optional[str] = None,
        asset_set_id: str,
        partial_failure: bool = False,
        validate_only: bool = False,
    ) -> Dict[str, Any]:
        """Remove an asset set link from a customer account.

        Args:
            customer_id: The customer ID
            asset_set_id: The asset set ID to unlink from the customer
            partial_failure: If true, valid operations succeed even if others fail
            validate_only: If true, only validates without executing

        Returns:
            Removal result details

        Example:
            result = await remove_customer_asset_set(
                customer_id="1234567890",
                asset_set_id="111"
            )
        """
        return await service.remove_customer_asset_set(
            ctx=ctx,
            customer_id=customer_id,
            asset_set_id=asset_set_id,
            partial_failure=partial_failure,
            validate_only=validate_only,
        )

    tools.extend([create_customer_asset_set, remove_customer_asset_set])
    return tools


def register_customer_asset_set_tools(
    mcp: FastMCP[Any],
) -> CustomerAssetSetService:
    """Register customer asset set tools with the MCP server.

    Returns the service instance for testing purposes.
    """
    service = CustomerAssetSetService()
    tools = create_customer_asset_set_tools(service)

    for tool in tools:
        mcp.tool(tool)

    return service
