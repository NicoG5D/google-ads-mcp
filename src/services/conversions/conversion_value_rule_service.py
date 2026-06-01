"""Conversion value rule service implementation using Google Ads SDK."""

from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastmcp import Context, FastMCP
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.v20.enums.types.conversion_value_rule_status import (
    ConversionValueRuleStatusEnum,
)
from google.ads.googleads.v20.enums.types.value_rule_device_type import (
    ValueRuleDeviceTypeEnum,
)
from google.ads.googleads.v20.enums.types.value_rule_geo_location_match_type import (
    ValueRuleGeoLocationMatchTypeEnum,
)
from google.ads.googleads.v20.enums.types.value_rule_operation import (
    ValueRuleOperationEnum,
)
from google.ads.googleads.v20.resources.types.conversion_value_rule import (
    ConversionValueRule,
)
from google.ads.googleads.v20.services.services.conversion_value_rule_service import (
    ConversionValueRuleServiceClient,
)
from google.ads.googleads.v20.services.services.google_ads_service import (
    GoogleAdsServiceClient,
)
from google.ads.googleads.v20.services.types.conversion_value_rule_service import (
    ConversionValueRuleOperation,
    MutateConversionValueRulesRequest,
    MutateConversionValueRulesResponse,
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


class ConversionValueRuleService:
    """Conversion value rule service for managing conversion value adjustments."""

    def __init__(self) -> None:
        self._client: Optional[ConversionValueRuleServiceClient] = None

    @property
    def client(self) -> ConversionValueRuleServiceClient:
        if self._client is None:
            sdk_client = get_sdk_client()
            self._client = sdk_client.client.get_service(
                "ConversionValueRuleService", version="v20"
            )
        assert self._client is not None
        return self._client

    async def create_conversion_value_rule(
        self,
        ctx: Context,
        *,
        customer_id: Optional[str] = None,
        action_operation: str,
        action_value: float,
        status: str = "ENABLED",
        device_types: Optional[List[str]] = None,
        geo_target_constants: Optional[List[str]] = None,
        user_list_ids: Optional[List[str]] = None,
        user_interest_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create a conversion value rule.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            action_operation: How to adjust the value - ADD, MULTIPLY, or SET
            action_value: The value to use with the operation
            status: ENABLED, PAUSED, or REMOVED
            device_types: Optional device condition - MOBILE, DESKTOP, TABLET
            geo_target_constants: Optional geo condition resource names
                (e.g. ["geoTargetConstants/2840"])
            user_list_ids: Optional audience condition - user list IDs
            user_interest_ids: Optional audience condition - user interest IDs

        Returns:
            Created conversion value rule details
        """
        try:
            customer_id = resolve_customer_id(customer_id)

            rule = ConversionValueRule()
            rule.status = resolve_enum(
                ConversionValueRuleStatusEnum.ConversionValueRuleStatus,
                status,
                "status",
            )

            # Set action
            rule.action.operation = resolve_enum(
                ValueRuleOperationEnum.ValueRuleOperation,
                action_operation,
                "action_operation",
            )
            rule.action.value = action_value

            # Device condition
            if device_types:
                for dt in device_types:
                    rule.device_condition.device_types.append(
                        resolve_enum(
                            ValueRuleDeviceTypeEnum.ValueRuleDeviceType,
                            dt,
                            "device_type",
                        )
                    )

            # Geo condition
            if geo_target_constants:
                rule.geo_location_condition.geo_target_constants.extend(
                    geo_target_constants
                )
                rule.geo_location_condition.geo_match_type = (
                    ValueRuleGeoLocationMatchTypeEnum.ValueRuleGeoLocationMatchType.ANY
                )

            # Audience condition
            if user_list_ids:
                rule.audience_condition.user_lists.extend(
                    [
                        f"customers/{customer_id}/userLists/{uid}"
                        for uid in user_list_ids
                    ]
                )
            if user_interest_ids:
                rule.audience_condition.user_interests.extend(
                    [
                        f"customers/{customer_id}/userInterests/{iid}"
                        for iid in user_interest_ids
                    ]
                )

            operation = ConversionValueRuleOperation()
            operation.create = rule

            request = MutateConversionValueRulesRequest()
            request.customer_id = customer_id
            request.operations = [operation]

            response: MutateConversionValueRulesResponse = (
                self.client.mutate_conversion_value_rules(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Created conversion value rule ({action_operation} {action_value})",
            )
            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to create conversion value rule: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def update_conversion_value_rule(
        self,
        ctx: Context,
        *,
        customer_id: Optional[str] = None,
        rule_resource_name: str,
        status: Optional[str] = None,
        action_operation: Optional[str] = None,
        action_value: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Update a conversion value rule.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            rule_resource_name: Resource name of the rule to update
            status: New status - ENABLED, PAUSED, or REMOVED
            action_operation: New operation - ADD, MULTIPLY, or SET
            action_value: New action value

        Returns:
            Updated conversion value rule details
        """
        try:
            customer_id = resolve_customer_id(customer_id)

            rule = ConversionValueRule()
            rule.resource_name = rule_resource_name

            update_mask_fields: List[str] = []

            if status is not None:
                rule.status = resolve_enum(
                    ConversionValueRuleStatusEnum.ConversionValueRuleStatus,
                    status,
                    "status",
                )
                update_mask_fields.append("status")

            if action_operation is not None:
                rule.action.operation = resolve_enum(
                    ValueRuleOperationEnum.ValueRuleOperation,
                    action_operation,
                    "action_operation",
                )
                update_mask_fields.append("action.operation")

            if action_value is not None:
                rule.action.value = action_value
                update_mask_fields.append("action.value")

            operation = ConversionValueRuleOperation()
            operation.update = rule
            operation.update_mask.CopyFrom(
                field_mask_pb2.FieldMask(paths=update_mask_fields)
            )

            request = MutateConversionValueRulesRequest()
            request.customer_id = customer_id
            request.operations = [operation]

            response = self.client.mutate_conversion_value_rules(request=request)

            await ctx.log(
                level="info",
                message=f"Updated conversion value rule {rule_resource_name}",
            )
            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to update conversion value rule: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def remove_conversion_value_rule(
        self,
        ctx: Context,
        *,
        customer_id: Optional[str] = None,
        rule_resource_name: str,
    ) -> Dict[str, Any]:
        """Remove a conversion value rule.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            rule_resource_name: Resource name of the rule to remove

        Returns:
            Removal result
        """
        try:
            customer_id = resolve_customer_id(customer_id)

            operation = ConversionValueRuleOperation()
            operation.remove = rule_resource_name

            request = MutateConversionValueRulesRequest()
            request.customer_id = customer_id
            request.operations = [operation]

            response = self.client.mutate_conversion_value_rules(request=request)

            await ctx.log(
                level="info",
                message=f"Removed conversion value rule {rule_resource_name}",
            )
            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to remove conversion value rule: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def list_conversion_value_rules(
        self,
        ctx: Context,
        *,
        customer_id: Optional[str] = None,
        status_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List conversion value rules.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            status_filter: Optional filter by status (ENABLED, PAUSED, REMOVED)

        Returns:
            List of conversion value rules
        """
        try:
            customer_id = resolve_customer_id(customer_id)

            sdk_client = get_sdk_client()
            google_ads_service: GoogleAdsServiceClient = sdk_client.client.get_service(
                "GoogleAdsService"
            )

            query = """
                SELECT
                    conversion_value_rule.resource_name,
                    conversion_value_rule.id,
                    conversion_value_rule.status,
                    conversion_value_rule.action.operation,
                    conversion_value_rule.action.value,
                    conversion_value_rule.owner_customer
                FROM conversion_value_rule
            """

            if status_filter:
                query += f" WHERE conversion_value_rule.status = '{status_filter}'"

            query += " ORDER BY conversion_value_rule.id"

            response = google_ads_service.search(customer_id=customer_id, query=query)

            rules = [serialize_proto_message(row) for row in response]

            await ctx.log(
                level="info",
                message=f"Found {len(rules)} conversion value rules",
            )
            return rules

        except Exception as e:
            error_msg = f"Failed to list conversion value rules: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e


def create_conversion_value_rule_tools(
    service: ConversionValueRuleService,
) -> List[Callable[..., Awaitable[Any]]]:
    """Create MCP tool functions for the conversion value rule service."""
    tools = []

    async def create_conversion_value_rule(
        ctx: Context,
        *,
        customer_id: Optional[str] = None,
        action_operation: str,
        action_value: float,
        status: str = "ENABLED",
        device_types: Optional[List[str]] = None,
        geo_target_constants: Optional[List[str]] = None,
        user_list_ids: Optional[List[str]] = None,
        user_interest_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create a conversion value rule that adjusts conversion values.

        Conversion value rules modify the reported value of conversions based
        on conditions (device, location, audience), helping Smart Bidding
        optimize toward higher-value conversions. After creating the rule,
        add its resource_name to a ConversionValueRuleSet to activate it.

        Args:
            customer_id: The customer ID
            action_operation: How to adjust the value:
                - ADD: add a fixed amount (e.g. action_value=5.0 adds $5)
                - MULTIPLY: multiply by a factor (e.g. action_value=1.5 = +50%)
                - SET: set to an absolute value
            action_value: Numeric value for the operation
            status: ENABLED, PAUSED, or REMOVED
            device_types: Optional device targeting: MOBILE, DESKTOP, TABLET
            geo_target_constants: Optional geo condition resource names
                (e.g. ["geoTargetConstants/2840"] for USA)
            user_list_ids: Optional audience condition — user list IDs
            user_interest_ids: Optional audience condition — user interest IDs

        Returns:
            Created rule details with resource_name and id
        """
        return await service.create_conversion_value_rule(
            ctx=ctx,
            customer_id=customer_id,
            action_operation=action_operation,
            action_value=action_value,
            status=status,
            device_types=device_types,
            geo_target_constants=geo_target_constants,
            user_list_ids=user_list_ids,
            user_interest_ids=user_interest_ids,
        )

    async def update_conversion_value_rule(
        ctx: Context,
        *,
        customer_id: Optional[str] = None,
        rule_resource_name: str,
        status: Optional[str] = None,
        action_operation: Optional[str] = None,
        action_value: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Update a conversion value rule.

        Args:
            customer_id: The customer ID
            rule_resource_name: Full resource name of the rule
            status: New status — ENABLED, PAUSED, or REMOVED
            action_operation: New operation — ADD, MULTIPLY, or SET
            action_value: New action value

        Returns:
            Updated rule details
        """
        return await service.update_conversion_value_rule(
            ctx=ctx,
            customer_id=customer_id,
            rule_resource_name=rule_resource_name,
            status=status,
            action_operation=action_operation,
            action_value=action_value,
        )

    async def remove_conversion_value_rule(
        ctx: Context,
        *,
        customer_id: Optional[str] = None,
        rule_resource_name: str,
    ) -> Dict[str, Any]:
        """Remove a conversion value rule.

        Args:
            customer_id: The customer ID
            rule_resource_name: Full resource name of the rule to remove

        Returns:
            Removal result
        """
        return await service.remove_conversion_value_rule(
            ctx=ctx,
            customer_id=customer_id,
            rule_resource_name=rule_resource_name,
        )

    async def list_conversion_value_rules(
        ctx: Context,
        *,
        customer_id: Optional[str] = None,
        status_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List conversion value rules.

        Args:
            customer_id: The customer ID
            status_filter: Optional status filter — ENABLED, PAUSED, or REMOVED

        Returns:
            List of conversion value rules with action and condition details
        """
        return await service.list_conversion_value_rules(
            ctx=ctx,
            customer_id=customer_id,
            status_filter=status_filter,
        )

    tools.extend(
        [
            create_conversion_value_rule,
            update_conversion_value_rule,
            remove_conversion_value_rule,
            list_conversion_value_rules,
        ]
    )
    return tools


def register_conversion_value_rule_tools(
    mcp: FastMCP[Any],
) -> ConversionValueRuleService:
    """Register conversion value rule tools with the MCP server."""
    service = ConversionValueRuleService()
    for tool in create_conversion_value_rule_tools(service):
        mcp.tool(tool)
    return service
