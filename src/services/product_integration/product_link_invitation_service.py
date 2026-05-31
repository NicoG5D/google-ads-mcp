"""Product Link Invitation service implementation with full v20 type safety."""

from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastmcp import Context, FastMCP
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.v20.enums.types.product_link_invitation_status import (
    ProductLinkInvitationStatusEnum,
)
from google.ads.googleads.v20.resources.types.product_link_invitation import (
    ProductLinkInvitation,
)
from google.ads.googleads.v20.services.services.product_link_invitation_service import (
    ProductLinkInvitationServiceClient,
)
from google.ads.googleads.v20.services.types.product_link_invitation_service import (
    CreateProductLinkInvitationRequest,
    CreateProductLinkInvitationResponse,
    RemoveProductLinkInvitationRequest,
    RemoveProductLinkInvitationResponse,
    UpdateProductLinkInvitationRequest,
    UpdateProductLinkInvitationResponse,
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


class ProductLinkInvitationService:
    """Service for managing product link invitations in Google Ads.

    Product link invitations represent invitations for data sharing
    connections between a Google Ads account and another account.
    """

    def __init__(self) -> None:
        self._client: Optional[ProductLinkInvitationServiceClient] = None

    @property
    def client(self) -> ProductLinkInvitationServiceClient:
        if self._client is None:
            sdk_client = get_sdk_client()
            self._client = sdk_client.client.get_service(
                "ProductLinkInvitationService", version="v20"
            )
        assert self._client is not None
        return self._client

    async def create_product_link_invitation(
        self,
        ctx: Context,
        customer_id: str,
        product_link_invitation: ProductLinkInvitation,
    ) -> Dict[str, Any]:
        """Create a product link invitation.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            product_link_invitation: The product link invitation to create

        Returns:
            Created product link invitation details
        """
        try:
            customer_id = format_customer_id(customer_id)

            request = CreateProductLinkInvitationRequest()
            request.customer_id = customer_id
            request.product_link_invitation = product_link_invitation

            response: CreateProductLinkInvitationResponse = (
                self.client.create_product_link_invitation(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Created product link invitation for customer {customer_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to create product link invitation: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def update_product_link_invitation(
        self,
        ctx: Context,
        customer_id: str,
        resource_name: str,
        product_link_invitation_status: ProductLinkInvitationStatusEnum.ProductLinkInvitationStatus,
    ) -> Dict[str, Any]:
        """Update the status of a product link invitation.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            resource_name: Resource name of the product link invitation to update
            product_link_invitation_status: New status for the invitation

        Returns:
            Updated product link invitation details
        """
        try:
            customer_id = format_customer_id(customer_id)

            request = UpdateProductLinkInvitationRequest()
            request.customer_id = customer_id
            request.resource_name = resource_name
            request.product_link_invitation_status = product_link_invitation_status

            response: UpdateProductLinkInvitationResponse = (
                self.client.update_product_link_invitation(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Updated product link invitation {resource_name} for customer {customer_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to update product link invitation: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def remove_product_link_invitation(
        self,
        ctx: Context,
        customer_id: str,
        resource_name: str,
    ) -> Dict[str, Any]:
        """Remove a product link invitation.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            resource_name: Resource name of the product link invitation to remove

        Returns:
            Removal result details
        """
        try:
            customer_id = format_customer_id(customer_id)

            request = RemoveProductLinkInvitationRequest()
            request.customer_id = customer_id
            request.resource_name = resource_name

            response: RemoveProductLinkInvitationResponse = (
                self.client.remove_product_link_invitation(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Removed product link invitation {resource_name} for customer {customer_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to remove product link invitation: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e


def create_product_link_invitation_tools(
    service: ProductLinkInvitationService,
) -> List[Callable[..., Awaitable[Any]]]:
    """Create tool functions for the product link invitation service."""
    tools = []

    async def create_product_link_invitation(
        ctx: Context,
        customer_id: str,
        linked_merchant_center_id: Optional[int] = None,
        linked_hotel_center_id: Optional[int] = None,
        linked_advertising_partner_customer: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a product link invitation between a Google Ads account and another account.

        Sends an invitation to establish a data sharing connection. The invited
        account must accept the invitation to complete the link.

        Args:
            customer_id: The customer ID
            linked_merchant_center_id: Merchant Center account ID to invite
            linked_hotel_center_id: Hotel Center account ID to invite
            linked_advertising_partner_customer: Resource name of the advertising
                partner Google Ads account to invite

        Returns:
            Created product link invitation resource name

        Example:
            result = await create_product_link_invitation(
                customer_id="1234567890",
                linked_merchant_center_id=111222333
            )
        """
        from google.ads.googleads.v20.resources.types.product_link_invitation import (
            AdvertisingPartnerLinkInvitationIdentifier,
            HotelCenterLinkInvitationIdentifier,
            MerchantCenterLinkInvitationIdentifier,
        )

        invitation = ProductLinkInvitation()

        if linked_merchant_center_id is not None:
            merchant_center = MerchantCenterLinkInvitationIdentifier()
            merchant_center.merchant_center_id = linked_merchant_center_id
            invitation.merchant_center = merchant_center
        elif linked_hotel_center_id is not None:
            hotel_center = HotelCenterLinkInvitationIdentifier()
            hotel_center.hotel_center_id = linked_hotel_center_id
            invitation.hotel_center = hotel_center
        elif linked_advertising_partner_customer is not None:
            advertising_partner = AdvertisingPartnerLinkInvitationIdentifier()
            advertising_partner.customer = linked_advertising_partner_customer
            invitation.advertising_partner = advertising_partner

        return await service.create_product_link_invitation(
            ctx=ctx,
            customer_id=customer_id,
            product_link_invitation=invitation,
        )

    async def update_product_link_invitation(
        ctx: Context,
        customer_id: str,
        resource_name: str,
        status: str,
    ) -> Dict[str, Any]:
        """Update the status of a product link invitation.

        Used to accept or reject an incoming product link invitation.

        Args:
            customer_id: The customer ID
            resource_name: Resource name of the product link invitation
                (e.g. customers/123/productLinkInvitations/456)
            status: New status - ACCEPTED or REJECTED

        Returns:
            Updated product link invitation resource name

        Example:
            result = await update_product_link_invitation(
                customer_id="1234567890",
                resource_name="customers/1234567890/productLinkInvitations/111",
                status="ACCEPTED"
            )
        """
        status_enum = resolve_enum(
            ProductLinkInvitationStatusEnum.ProductLinkInvitationStatus,
            status,
            "status",
        )
        return await service.update_product_link_invitation(
            ctx=ctx,
            customer_id=customer_id,
            resource_name=resource_name,
            product_link_invitation_status=status_enum,
        )

    async def remove_product_link_invitation(
        ctx: Context,
        customer_id: str,
        resource_name: str,
    ) -> Dict[str, Any]:
        """Remove a product link invitation.

        Args:
            customer_id: The customer ID
            resource_name: Resource name of the product link invitation to remove
                (e.g. customers/123/productLinkInvitations/456)

        Returns:
            Removed product link invitation resource name

        Example:
            result = await remove_product_link_invitation(
                customer_id="1234567890",
                resource_name="customers/1234567890/productLinkInvitations/111"
            )
        """
        return await service.remove_product_link_invitation(
            ctx=ctx,
            customer_id=customer_id,
            resource_name=resource_name,
        )

    tools.extend(
        [
            create_product_link_invitation,
            update_product_link_invitation,
            remove_product_link_invitation,
        ]
    )
    return tools


def register_product_link_invitation_tools(
    mcp: FastMCP[Any],
) -> ProductLinkInvitationService:
    """Register product link invitation tools with the MCP server.

    Returns the service instance for testing purposes.
    """
    service = ProductLinkInvitationService()
    tools = create_product_link_invitation_tools(service)

    for tool in tools:
        mcp.tool(tool)

    return service
