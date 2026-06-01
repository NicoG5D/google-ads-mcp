"""Smart Campaign Setting service implementation with full v20 type safety."""

from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastmcp import Context, FastMCP
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.v20.enums.types.response_content_type import (
    ResponseContentTypeEnum,
)
from google.ads.googleads.v20.resources.types.smart_campaign_setting import (
    SmartCampaignSetting,
)
from google.ads.googleads.v20.services.services.smart_campaign_setting_service import (
    SmartCampaignSettingServiceClient,
)
from google.ads.googleads.v20.services.types.smart_campaign_setting_service import (
    GetSmartCampaignStatusRequest,
    GetSmartCampaignStatusResponse,
    MutateSmartCampaignSettingsRequest,
    MutateSmartCampaignSettingsResponse,
    SmartCampaignSettingOperation,
)
from google.protobuf import field_mask_pb2

from src.sdk_client import get_sdk_client
from src.utils import (
    format_ads_error,
    resolve_customer_id,
    get_logger,
    serialize_proto_message,
)

logger = get_logger(__name__)


class SmartCampaignSettingService:
    """Service for managing smart campaign settings in Google Ads.

    Smart campaign settings control the landing page, business info, phone
    number, and language for simplified Smart campaigns.
    """

    def __init__(self) -> None:
        self._client: Optional[SmartCampaignSettingServiceClient] = None

    @property
    def client(self) -> SmartCampaignSettingServiceClient:
        if self._client is None:
            sdk_client = get_sdk_client()
            self._client = sdk_client.client.get_service(
                "SmartCampaignSettingService", version="v20"
            )
        assert self._client is not None
        return self._client

    async def get_smart_campaign_status(
        self,
        ctx: Context,
        *,
        customer_id: Optional[str] = None,
        campaign_id: str,
    ) -> Dict[str, Any]:
        """Get the status of a Smart campaign.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            campaign_id: The campaign ID to get status for

        Returns:
            Smart campaign status details including eligibility information
        """
        try:
            customer_id = resolve_customer_id(customer_id)
            resource_name = (
                f"customers/{customer_id}/smartCampaignSettings/{campaign_id}"
            )

            request = GetSmartCampaignStatusRequest()
            request.resource_name = resource_name

            response: GetSmartCampaignStatusResponse = (
                self.client.get_smart_campaign_status(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Retrieved smart campaign status for campaign {campaign_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to get smart campaign status: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def update_smart_campaign_setting(
        self,
        ctx: Context,
        *,
        customer_id: Optional[str] = None,
        campaign_id: str,
        advertising_language_code: Optional[str] = None,
        final_url: Optional[str] = None,
        business_name: Optional[str] = None,
        business_profile_location: Optional[str] = None,
        phone_number: Optional[str] = None,
        phone_country_code: Optional[str] = None,
        include_lead_form: Optional[bool] = None,
        partial_failure: bool = False,
        validate_only: bool = False,
        response_content_type: ResponseContentTypeEnum.ResponseContentType = ResponseContentTypeEnum.ResponseContentType.MUTABLE_RESOURCE,
    ) -> Dict[str, Any]:
        """Update a Smart campaign setting.

        Only update fields are supported — Smart campaign settings cannot be created
        directly; they are auto-created when a Smart campaign is created.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            campaign_id: The campaign ID whose settings to update
            advertising_language_code: Language code to advertise in (e.g., "en")
            final_url: Landing page URL for the campaign
            business_name: Business name (mutually exclusive with business_profile_location)
            business_profile_location: Business Profile location resource name
                (mutually exclusive with business_name)
            phone_number: Phone number for the Smart campaign
            phone_country_code: Two-letter ISO country code for the phone number
            include_lead_form: Whether to include a lead form on business profile landing page
                (only applicable when using ad_optimized_business_profile_setting)
            partial_failure: If true, valid operations succeed even if others fail
            validate_only: If true, only validates without executing
            response_content_type: What to return in response

        Returns:
            Updated smart campaign setting details
        """
        try:
            customer_id = resolve_customer_id(customer_id)
            resource_name = (
                f"customers/{customer_id}/smartCampaignSettings/{campaign_id}"
            )

            setting = SmartCampaignSetting()
            setting.resource_name = resource_name

            update_fields = []

            if advertising_language_code is not None:
                setting.advertising_language_code = advertising_language_code
                update_fields.append("advertising_language_code")

            if final_url is not None:
                setting.final_url = final_url
                update_fields.append("final_url")
            elif include_lead_form is not None:
                ad_opt = SmartCampaignSetting.AdOptimizedBusinessProfileSetting()
                ad_opt.include_lead_form = include_lead_form
                setting.ad_optimized_business_profile_setting = ad_opt
                update_fields.append("ad_optimized_business_profile_setting")

            if business_name is not None:
                setting.business_name = business_name
                update_fields.append("business_name")
            elif business_profile_location is not None:
                setting.business_profile_location = business_profile_location
                update_fields.append("business_profile_location")

            if phone_number is not None or phone_country_code is not None:
                phone = SmartCampaignSetting.PhoneNumber()
                if phone_number is not None:
                    phone.phone_number = phone_number
                    update_fields.append("phone_number.phone_number")
                if phone_country_code is not None:
                    phone.country_code = phone_country_code
                    update_fields.append("phone_number.country_code")
                setting.phone_number = phone

            operation = SmartCampaignSettingOperation()
            operation.update = setting
            operation.update_mask = field_mask_pb2.FieldMask(paths=update_fields)

            request = MutateSmartCampaignSettingsRequest()
            request.customer_id = customer_id
            request.operations = [operation]
            request.partial_failure = partial_failure
            request.validate_only = validate_only
            request.response_content_type = response_content_type

            response: MutateSmartCampaignSettingsResponse = (
                self.client.mutate_smart_campaign_settings(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Updated smart campaign setting for campaign {campaign_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to update smart campaign setting: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e


def create_smart_campaign_setting_tools(
    service: SmartCampaignSettingService,
) -> List[Callable[..., Awaitable[Any]]]:
    """Create tool functions for the smart campaign setting service."""
    tools = []

    async def get_smart_campaign_status(
        ctx: Context,
        *,
        customer_id: Optional[str] = None,
        campaign_id: str,
    ) -> Dict[str, Any]:
        """Get the status of a Smart campaign.

        Returns detailed status information about whether the campaign is eligible
        to serve, paused, removed, or has ended, including relevant timestamps.

        Args:
            customer_id: The customer ID
            campaign_id: The campaign ID to get status for

        Returns:
            Smart campaign status including smart_campaign_status field and
            status-specific details (not_eligible_details, eligible_details,
            paused_details, removed_details, or ended_details)

        Example:
            result = await get_smart_campaign_status(
                customer_id="1234567890",
                campaign_id="9876543210"
            )
        """
        return await service.get_smart_campaign_status(
            ctx=ctx,
            customer_id=customer_id,
            campaign_id=campaign_id,
        )

    async def update_smart_campaign_setting(
        ctx: Context,
        *,
        customer_id: Optional[str] = None,
        campaign_id: str,
        advertising_language_code: Optional[str] = None,
        final_url: Optional[str] = None,
        business_name: Optional[str] = None,
        business_profile_location: Optional[str] = None,
        phone_number: Optional[str] = None,
        phone_country_code: Optional[str] = None,
        include_lead_form: Optional[bool] = None,
        partial_failure: bool = False,
        validate_only: bool = False,
    ) -> Dict[str, Any]:
        """Update settings for a Smart campaign.

        Smart campaign settings are auto-created with the campaign. Use this to
        update the landing page, business info, phone number, and language.

        Note: final_url and ad_optimized_business_profile_setting are mutually exclusive
        (landing_page oneof). business_name and business_profile_location are also
        mutually exclusive (business_setting oneof).

        Args:
            customer_id: The customer ID
            campaign_id: The campaign ID whose settings to update
            advertising_language_code: Language code (e.g., "en", "fr", "de")
            final_url: Landing page URL for the campaign
            business_name: Business name (cannot be set with business_profile_location)
            business_profile_location: Business Profile location resource name
                (cannot be set with business_name)
            phone_number: Phone number for the Smart campaign
            phone_country_code: Two-letter ISO country code (e.g., "US")
            include_lead_form: Include lead form on business profile landing page
                (only used when landing page is set to business profile)
            partial_failure: If true, valid operations succeed even if others fail
            validate_only: If true, only validates without executing

        Returns:
            Updated smart campaign setting details

        Example:
            result = await update_smart_campaign_setting(
                customer_id="1234567890",
                campaign_id="9876543210",
                final_url="https://example.com/landing",
                advertising_language_code="en",
                business_name="My Business",
                phone_number="+15551234567",
                phone_country_code="US"
            )
        """
        return await service.update_smart_campaign_setting(
            ctx=ctx,
            customer_id=customer_id,
            campaign_id=campaign_id,
            advertising_language_code=advertising_language_code,
            final_url=final_url,
            business_name=business_name,
            business_profile_location=business_profile_location,
            phone_number=phone_number,
            phone_country_code=phone_country_code,
            include_lead_form=include_lead_form,
            partial_failure=partial_failure,
            validate_only=validate_only,
        )

    tools.extend([get_smart_campaign_status, update_smart_campaign_setting])
    return tools


def register_smart_campaign_setting_tools(
    mcp: FastMCP[Any],
) -> SmartCampaignSettingService:
    """Register smart campaign setting tools with the MCP server.

    Returns the service instance for testing purposes.
    """
    service = SmartCampaignSettingService()
    tools = create_smart_campaign_setting_tools(service)

    for tool in tools:
        mcp.tool(tool)

    return service
