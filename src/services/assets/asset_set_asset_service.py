"""Asset Set Asset service implementation with full v20 type safety."""

from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastmcp import Context, FastMCP
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.v20.enums.types.response_content_type import (
    ResponseContentTypeEnum,
)
from google.ads.googleads.v20.resources.types.asset_set_asset import AssetSetAsset
from google.ads.googleads.v20.services.services.asset_set_asset_service import (
    AssetSetAssetServiceClient,
)
from google.ads.googleads.v20.services.types.asset_set_asset_service import (
    AssetSetAssetOperation,
    MutateAssetSetAssetsRequest,
    MutateAssetSetAssetsResponse,
)

from src.sdk_client import get_sdk_client
from src.utils import (
    format_ads_error,
    format_customer_id,
    get_logger,
    serialize_proto_message,
)

logger = get_logger(__name__)


class AssetSetAssetService:
    """Service for managing asset set assets in Google Ads.

    AssetSetAsset represents the link between an asset and an asset set.
    """

    def __init__(self) -> None:
        self._client: Optional[AssetSetAssetServiceClient] = None

    @property
    def client(self) -> AssetSetAssetServiceClient:
        if self._client is None:
            sdk_client = get_sdk_client()
            self._client = sdk_client.client.get_service(
                "AssetSetAssetService", version="v20"
            )
        assert self._client is not None
        return self._client

    async def create_asset_set_asset(
        self,
        ctx: Context,
        customer_id: str,
        asset_set: str,
        asset: str,
        partial_failure: bool = False,
        validate_only: bool = False,
        response_content_type: ResponseContentTypeEnum.ResponseContentType = ResponseContentTypeEnum.ResponseContentType.MUTABLE_RESOURCE,
    ) -> Dict[str, Any]:
        """Link an asset to an asset set.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            asset_set: The resource name of the asset set to link to
            asset: The resource name of the asset to link
            partial_failure: If true, valid operations succeed even if others fail
            validate_only: If true, only validates without executing
            response_content_type: What to return in response

        Returns:
            Created asset set asset link details
        """
        try:
            customer_id = format_customer_id(customer_id)

            asset_set_asset = AssetSetAsset()
            asset_set_asset.asset_set = asset_set
            asset_set_asset.asset = asset

            operation = AssetSetAssetOperation()
            operation.create = asset_set_asset

            request = MutateAssetSetAssetsRequest()
            request.customer_id = customer_id
            request.operations = [operation]
            request.partial_failure = partial_failure
            request.validate_only = validate_only
            request.response_content_type = response_content_type

            response: MutateAssetSetAssetsResponse = (
                self.client.mutate_asset_set_assets(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Linked asset {asset} to asset set {asset_set} for customer {customer_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to create asset set asset: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def remove_asset_set_asset(
        self,
        ctx: Context,
        customer_id: str,
        asset_set_id: str,
        asset_id: str,
        partial_failure: bool = False,
        validate_only: bool = False,
    ) -> Dict[str, Any]:
        """Remove an asset from an asset set.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            asset_set_id: The asset set ID
            asset_id: The asset ID to unlink
            partial_failure: If true, valid operations succeed even if others fail
            validate_only: If true, only validates without executing

        Returns:
            Removal result details
        """
        try:
            customer_id = format_customer_id(customer_id)
            resource_name = f"customers/{customer_id}/assetSetAssets/{asset_set_id}~{asset_id}"

            operation = AssetSetAssetOperation()
            operation.remove = resource_name

            request = MutateAssetSetAssetsRequest()
            request.customer_id = customer_id
            request.operations = [operation]
            request.partial_failure = partial_failure
            request.validate_only = validate_only

            response: MutateAssetSetAssetsResponse = (
                self.client.mutate_asset_set_assets(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Removed asset {asset_id} from asset set {asset_set_id} for customer {customer_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to remove asset set asset: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e


def create_asset_set_asset_tools(
    service: AssetSetAssetService,
) -> List[Callable[..., Awaitable[Any]]]:
    """Create tool functions for the asset set asset service."""
    tools = []

    async def create_asset_set_asset(
        ctx: Context,
        customer_id: str,
        asset_set: str,
        asset: str,
        partial_failure: bool = False,
        validate_only: bool = False,
    ) -> Dict[str, Any]:
        """Link an asset to an asset set.

        Creates an AssetSetAsset which represents the link between an asset
        and an asset set. Adding this link makes the asset available within
        the asset set for use in campaigns.

        Args:
            customer_id: The customer ID
            asset_set: Resource name of the asset set (e.g. customers/123/assetSets/456)
            asset: Resource name of the asset to link (e.g. customers/123/assets/789)
            partial_failure: If true, valid operations succeed even if others fail
            validate_only: If true, only validates without executing

        Returns:
            Created asset set asset link details

        Example:
            result = await create_asset_set_asset(
                customer_id="1234567890",
                asset_set="customers/1234567890/assetSets/111",
                asset="customers/1234567890/assets/222"
            )
        """
        return await service.create_asset_set_asset(
            ctx=ctx,
            customer_id=customer_id,
            asset_set=asset_set,
            asset=asset,
            partial_failure=partial_failure,
            validate_only=validate_only,
        )

    async def remove_asset_set_asset(
        ctx: Context,
        customer_id: str,
        asset_set_id: str,
        asset_id: str,
        partial_failure: bool = False,
        validate_only: bool = False,
    ) -> Dict[str, Any]:
        """Remove an asset from an asset set.

        Args:
            customer_id: The customer ID
            asset_set_id: The asset set ID
            asset_id: The asset ID to unlink from the asset set
            partial_failure: If true, valid operations succeed even if others fail
            validate_only: If true, only validates without executing

        Returns:
            Removal result details

        Example:
            result = await remove_asset_set_asset(
                customer_id="1234567890",
                asset_set_id="111",
                asset_id="222"
            )
        """
        return await service.remove_asset_set_asset(
            ctx=ctx,
            customer_id=customer_id,
            asset_set_id=asset_set_id,
            asset_id=asset_id,
            partial_failure=partial_failure,
            validate_only=validate_only,
        )

    tools.extend([create_asset_set_asset, remove_asset_set_asset])
    return tools


def register_asset_set_asset_tools(
    mcp: FastMCP[Any],
) -> AssetSetAssetService:
    """Register asset set asset tools with the MCP server.

    Returns the service instance for testing purposes.
    """
    service = AssetSetAssetService()
    tools = create_asset_set_asset_tools(service)

    for tool in tools:
        mcp.tool(tool)

    return service
