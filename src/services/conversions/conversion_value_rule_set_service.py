"""Conversion Value Rule Set service implementation with full v20 type safety."""

from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastmcp import Context, FastMCP
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.v20.enums.types.conversion_action_category import (
    ConversionActionCategoryEnum,
)
from google.ads.googleads.v20.enums.types.response_content_type import (
    ResponseContentTypeEnum,
)
from google.ads.googleads.v20.enums.types.value_rule_set_attachment_type import (
    ValueRuleSetAttachmentTypeEnum,
)
from google.ads.googleads.v20.enums.types.value_rule_set_dimension import (
    ValueRuleSetDimensionEnum,
)
from google.ads.googleads.v20.resources.types.conversion_value_rule_set import (
    ConversionValueRuleSet,
)
from google.ads.googleads.v20.services.services.conversion_value_rule_set_service import (
    ConversionValueRuleSetServiceClient,
)
from google.ads.googleads.v20.services.types.conversion_value_rule_set_service import (
    ConversionValueRuleSetOperation,
    MutateConversionValueRuleSetsRequest,
    MutateConversionValueRuleSetsResponse,
)
from google.protobuf import field_mask_pb2

from src.sdk_client import get_sdk_client
from src.utils import (
    format_ads_error,
    resolve_customer_id,
    get_logger,
    resolve_enum,
    serialize_proto_message,
)

logger = get_logger(__name__)


class ConversionValueRuleSetService:
    """Service for managing conversion value rule sets in Google Ads.

    Conversion value rule sets group conversion value rules by dimension
    (e.g., GEO_LOCATION, DEVICE, AUDIENCE) to adjust conversion values
    based on customer attributes.
    """

    def __init__(self) -> None:
        self._client: Optional[ConversionValueRuleSetServiceClient] = None

    @property
    def client(self) -> ConversionValueRuleSetServiceClient:
        if self._client is None:
            sdk_client = get_sdk_client()
            self._client = sdk_client.client.get_service(
                "ConversionValueRuleSetService", version="v20"
            )
        assert self._client is not None
        return self._client

    async def create_conversion_value_rule_set(
        self,
        ctx: Context,
        *,
        customer_id: Optional[str] = None,
        dimensions: List[ValueRuleSetDimensionEnum.ValueRuleSetDimension],
        attachment_type: ValueRuleSetAttachmentTypeEnum.ValueRuleSetAttachmentType,
        conversion_action_categories: List[
            ConversionActionCategoryEnum.ConversionActionCategory
        ],
        conversion_value_rules: Optional[List[str]] = None,
        campaign_id: Optional[str] = None,
        partial_failure: bool = False,
        validate_only: bool = False,
        response_content_type: ResponseContentTypeEnum.ResponseContentType = ResponseContentTypeEnum.ResponseContentType.MUTABLE_RESOURCE,
    ) -> Dict[str, Any]:
        """Create a new conversion value rule set.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            dimensions: Dimensions that define conditions for value rules in this set
                (first entry is the primary dimension)
            attachment_type: Scope — CUSTOMER or CAMPAIGN level attachment
            conversion_action_categories: Conversion action categories this rule set applies to
            conversion_value_rules: Optional list of conversion value rule resource names to include
            campaign_id: Campaign ID (required when attachment_type is CAMPAIGN)
            partial_failure: If true, valid operations succeed even if others fail
            validate_only: If true, only validates without executing
            response_content_type: What to return in response

        Returns:
            Created conversion value rule set details
        """
        try:
            customer_id = resolve_customer_id(customer_id)

            rule_set = ConversionValueRuleSet()
            rule_set.dimensions = dimensions
            rule_set.attachment_type = attachment_type
            rule_set.conversion_action_categories = conversion_action_categories

            if conversion_value_rules:
                rule_set.conversion_value_rules = conversion_value_rules

            if campaign_id is not None:
                rule_set.campaign = f"customers/{customer_id}/campaigns/{campaign_id}"

            operation = ConversionValueRuleSetOperation()
            operation.create = rule_set

            request = MutateConversionValueRuleSetsRequest()
            request.customer_id = customer_id
            request.operations = [operation]
            request.partial_failure = partial_failure
            request.validate_only = validate_only
            request.response_content_type = response_content_type

            response: MutateConversionValueRuleSetsResponse = (
                self.client.mutate_conversion_value_rule_sets(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Created conversion value rule set for customer {customer_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to create conversion value rule set: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def update_conversion_value_rule_set(
        self,
        ctx: Context,
        *,
        customer_id: Optional[str] = None,
        conversion_value_rule_set_id: str,
        conversion_value_rules: Optional[List[str]] = None,
        dimensions: Optional[
            List[ValueRuleSetDimensionEnum.ValueRuleSetDimension]
        ] = None,
        partial_failure: bool = False,
        validate_only: bool = False,
        response_content_type: ResponseContentTypeEnum.ResponseContentType = ResponseContentTypeEnum.ResponseContentType.MUTABLE_RESOURCE,
    ) -> Dict[str, Any]:
        """Update an existing conversion value rule set.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            conversion_value_rule_set_id: The conversion value rule set ID to update
            conversion_value_rules: New list of conversion value rule resource names
            dimensions: New list of dimensions for value rule conditions
            partial_failure: If true, valid operations succeed even if others fail
            validate_only: If true, only validates without executing
            response_content_type: What to return in response

        Returns:
            Updated conversion value rule set details
        """
        try:
            customer_id = resolve_customer_id(customer_id)
            resource_name = (
                f"customers/{customer_id}/conversionValueRuleSets/"
                f"{conversion_value_rule_set_id}"
            )

            rule_set = ConversionValueRuleSet()
            rule_set.resource_name = resource_name

            update_fields = []

            if conversion_value_rules is not None:
                rule_set.conversion_value_rules = conversion_value_rules
                update_fields.append("conversion_value_rules")

            if dimensions is not None:
                rule_set.dimensions = dimensions
                update_fields.append("dimensions")

            operation = ConversionValueRuleSetOperation()
            operation.update = rule_set
            operation.update_mask = field_mask_pb2.FieldMask(paths=update_fields)

            request = MutateConversionValueRuleSetsRequest()
            request.customer_id = customer_id
            request.operations = [operation]
            request.partial_failure = partial_failure
            request.validate_only = validate_only
            request.response_content_type = response_content_type

            response: MutateConversionValueRuleSetsResponse = (
                self.client.mutate_conversion_value_rule_sets(request=request)
            )

            await ctx.log(
                level="info",
                message=(
                    f"Updated conversion value rule set {conversion_value_rule_set_id} "
                    f"for customer {customer_id}"
                ),
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to update conversion value rule set: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def remove_conversion_value_rule_set(
        self,
        ctx: Context,
        *,
        customer_id: Optional[str] = None,
        conversion_value_rule_set_id: str,
        partial_failure: bool = False,
        validate_only: bool = False,
    ) -> Dict[str, Any]:
        """Remove a conversion value rule set.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            conversion_value_rule_set_id: The conversion value rule set ID to remove
            partial_failure: If true, valid operations succeed even if others fail
            validate_only: If true, only validates without executing

        Returns:
            Removal result details
        """
        try:
            customer_id = resolve_customer_id(customer_id)
            resource_name = (
                f"customers/{customer_id}/conversionValueRuleSets/"
                f"{conversion_value_rule_set_id}"
            )

            operation = ConversionValueRuleSetOperation()
            operation.remove = resource_name

            request = MutateConversionValueRuleSetsRequest()
            request.customer_id = customer_id
            request.operations = [operation]
            request.partial_failure = partial_failure
            request.validate_only = validate_only

            response = self.client.mutate_conversion_value_rule_sets(request=request)

            await ctx.log(
                level="info",
                message=(
                    f"Removed conversion value rule set {conversion_value_rule_set_id} "
                    f"for customer {customer_id}"
                ),
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to remove conversion value rule set: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e


def create_conversion_value_rule_set_tools(
    service: ConversionValueRuleSetService,
) -> List[Callable[..., Awaitable[Any]]]:
    """Create tool functions for the conversion value rule set service."""
    tools = []

    async def create_conversion_value_rule_set(
        ctx: Context,
        *,
        customer_id: Optional[str] = None,
        dimensions: List[str],
        attachment_type: str,
        conversion_action_categories: List[str],
        conversion_value_rules: Optional[List[str]] = None,
        campaign_id: Optional[str] = None,
        partial_failure: bool = False,
        validate_only: bool = False,
    ) -> Dict[str, Any]:
        """Create a conversion value rule set to group value rules by dimension.

        A conversion value rule set defines which dimensions (GEO_LOCATION, DEVICE,
        AUDIENCE) apply to value rules and which conversion actions are affected.

        Args:
            customer_id: The customer ID
            dimensions: Dimensions for this rule set. Values: GEO_LOCATION, DEVICE,
                AUDIENCE, NO_CONDITION. First entry is the primary dimension.
            attachment_type: Scope of the rule set. Values: CUSTOMER or CAMPAIGN
            conversion_action_categories: Conversion action categories this applies to.
                Values: DEFAULT, PAGE_VIEW, PURCHASE, SIGNUP, LEAD, DOWNLOAD,
                ADD_TO_CART, BEGIN_CHECKOUT, SUBSCRIBE_PAID, PHONE_CALL_LEAD,
                IMPORTED_LEAD, SUBMIT_LEAD_FORM, BOOK_APPOINTMENT, REQUEST_QUOTE,
                GET_DIRECTIONS, OUTBOUND_CLICK, CONTACT, ENGAGEMENT, STORE_VISIT,
                STORE_SALE, QUALIFIED_LEAD, CONVERTED_LEAD
            conversion_value_rules: Resource names of conversion value rules to include
            campaign_id: Campaign ID (required when attachment_type is CAMPAIGN)
            partial_failure: If true, valid operations succeed even if others fail
            validate_only: If true, only validates without executing

        Returns:
            Created conversion value rule set details

        Example:
            result = await create_conversion_value_rule_set(
                customer_id="1234567890",
                dimensions=["GEO_LOCATION"],
                attachment_type="CUSTOMER",
                conversion_action_categories=["DEFAULT"],
                conversion_value_rules=[
                    "customers/1234567890/conversionValueRules/111"
                ]
            )
        """
        dimension_enums = [
            resolve_enum(
                ValueRuleSetDimensionEnum.ValueRuleSetDimension,
                d,
                "dimensions",
            )
            for d in dimensions
        ]
        attachment_enum = resolve_enum(
            ValueRuleSetAttachmentTypeEnum.ValueRuleSetAttachmentType,
            attachment_type,
            "attachment_type",
        )
        category_enums = [
            resolve_enum(
                ConversionActionCategoryEnum.ConversionActionCategory,
                c,
                "conversion_action_categories",
            )
            for c in conversion_action_categories
        ]
        return await service.create_conversion_value_rule_set(
            ctx=ctx,
            customer_id=customer_id,
            dimensions=dimension_enums,
            attachment_type=attachment_enum,
            conversion_action_categories=category_enums,
            conversion_value_rules=conversion_value_rules,
            campaign_id=campaign_id,
            partial_failure=partial_failure,
            validate_only=validate_only,
        )

    async def update_conversion_value_rule_set(
        ctx: Context,
        *,
        customer_id: Optional[str] = None,
        conversion_value_rule_set_id: str,
        conversion_value_rules: Optional[List[str]] = None,
        dimensions: Optional[List[str]] = None,
        partial_failure: bool = False,
        validate_only: bool = False,
    ) -> Dict[str, Any]:
        """Update an existing conversion value rule set.

        Args:
            customer_id: The customer ID
            conversion_value_rule_set_id: The conversion value rule set ID to update
            conversion_value_rules: New list of conversion value rule resource names
            dimensions: New list of dimensions. Values: GEO_LOCATION, DEVICE,
                AUDIENCE, NO_CONDITION
            partial_failure: If true, valid operations succeed even if others fail
            validate_only: If true, only validates without executing

        Returns:
            Updated conversion value rule set details

        Example:
            result = await update_conversion_value_rule_set(
                customer_id="1234567890",
                conversion_value_rule_set_id="222333444",
                conversion_value_rules=[
                    "customers/1234567890/conversionValueRules/111",
                    "customers/1234567890/conversionValueRules/222"
                ]
            )
        """
        dimension_enums: Optional[
            List[ValueRuleSetDimensionEnum.ValueRuleSetDimension]
        ] = None
        if dimensions is not None:
            dimension_enums = [
                resolve_enum(
                    ValueRuleSetDimensionEnum.ValueRuleSetDimension,
                    d,
                    "dimensions",
                )
                for d in dimensions
            ]
        return await service.update_conversion_value_rule_set(
            ctx=ctx,
            customer_id=customer_id,
            conversion_value_rule_set_id=conversion_value_rule_set_id,
            conversion_value_rules=conversion_value_rules,
            dimensions=dimension_enums,
            partial_failure=partial_failure,
            validate_only=validate_only,
        )

    async def remove_conversion_value_rule_set(
        ctx: Context,
        *,
        customer_id: Optional[str] = None,
        conversion_value_rule_set_id: str,
        partial_failure: bool = False,
        validate_only: bool = False,
    ) -> Dict[str, Any]:
        """Remove a conversion value rule set.

        Args:
            customer_id: The customer ID
            conversion_value_rule_set_id: The conversion value rule set ID to remove
            partial_failure: If true, valid operations succeed even if others fail
            validate_only: If true, only validates without executing

        Returns:
            Removal result details

        Example:
            result = await remove_conversion_value_rule_set(
                customer_id="1234567890",
                conversion_value_rule_set_id="222333444"
            )
        """
        return await service.remove_conversion_value_rule_set(
            ctx=ctx,
            customer_id=customer_id,
            conversion_value_rule_set_id=conversion_value_rule_set_id,
            partial_failure=partial_failure,
            validate_only=validate_only,
        )

    tools.extend(
        [
            create_conversion_value_rule_set,
            update_conversion_value_rule_set,
            remove_conversion_value_rule_set,
        ]
    )
    return tools


def register_conversion_value_rule_set_tools(
    mcp: FastMCP[Any],
) -> ConversionValueRuleSetService:
    """Register conversion value rule set tools with the MCP server.

    Returns the service instance for testing purposes.
    """
    service = ConversionValueRuleSetService()
    tools = create_conversion_value_rule_set_tools(service)

    for tool in tools:
        mcp.tool(tool)

    return service
