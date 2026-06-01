"""Customer Lifecycle Goal service implementation with full v20 type safety."""

from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastmcp import Context, FastMCP
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.v20.common.types.lifecycle_goals import (
    LifecycleGoalValueSettings,
)
from google.ads.googleads.v20.resources.types.customer_lifecycle_goal import (
    CustomerLifecycleGoal,
)
from google.ads.googleads.v20.services.services.customer_lifecycle_goal_service import (
    CustomerLifecycleGoalServiceClient,
)
from google.ads.googleads.v20.services.types.customer_lifecycle_goal_service import (
    ConfigureCustomerLifecycleGoalsRequest,
    ConfigureCustomerLifecycleGoalsResponse,
    CustomerLifecycleGoalOperation,
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


class CustomerLifecycleGoalService:
    """Service for configuring customer lifecycle goals in Google Ads.

    Customer lifecycle goals set account-level value settings used when
    campaigns optimize for customer acquisition objectives.
    """

    def __init__(self) -> None:
        self._client: Optional[CustomerLifecycleGoalServiceClient] = None

    @property
    def client(self) -> CustomerLifecycleGoalServiceClient:
        if self._client is None:
            sdk_client = get_sdk_client()
            self._client = sdk_client.client.get_service(
                "CustomerLifecycleGoalService", version="v20"
            )
        assert self._client is not None
        return self._client

    async def create_customer_lifecycle_goal(
        self,
        ctx: Context,
        *,
        customer_id: Optional[str] = None,
        value: Optional[float] = None,
        high_lifetime_value: Optional[float] = None,
        validate_only: bool = False,
    ) -> Dict[str, Any]:
        """Create customer lifecycle goal value settings.

        Sets the account-level customer acquisition goal value settings. These
        values are used as defaults when campaigns do not set campaign-level overrides.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            value: Incremental conversion value for new non-high-value customers
            high_lifetime_value: Incremental conversion value for new high-value customers
            validate_only: If true, only validates without executing

        Returns:
            Configuration result details
        """
        try:
            customer_id = resolve_customer_id(customer_id)
            resource_name = f"customers/{customer_id}/customerLifecycleGoal"

            lifecycle_goal = CustomerLifecycleGoal()
            lifecycle_goal.resource_name = resource_name

            if value is not None or high_lifetime_value is not None:
                value_settings = LifecycleGoalValueSettings()
                if value is not None:
                    value_settings.value = value
                if high_lifetime_value is not None:
                    value_settings.high_lifetime_value = high_lifetime_value
                lifecycle_goal.customer_acquisition_goal_value_settings = value_settings

            operation = CustomerLifecycleGoalOperation()
            operation.create = lifecycle_goal

            request = ConfigureCustomerLifecycleGoalsRequest()
            request.customer_id = customer_id
            request.operation = operation
            request.validate_only = validate_only

            response: ConfigureCustomerLifecycleGoalsResponse = (
                self.client.configure_customer_lifecycle_goals(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Created customer lifecycle goal for customer {customer_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to create customer lifecycle goal: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def update_customer_lifecycle_goal(
        self,
        ctx: Context,
        *,
        customer_id: Optional[str] = None,
        value: Optional[float] = None,
        high_lifetime_value: Optional[float] = None,
        validate_only: bool = False,
    ) -> Dict[str, Any]:
        """Update the customer lifecycle goal value settings.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            value: New incremental conversion value for new non-high-value customers
            high_lifetime_value: New incremental conversion value for high-value customers
            validate_only: If true, only validates without executing

        Returns:
            Configuration result details
        """
        try:
            customer_id = resolve_customer_id(customer_id)
            resource_name = f"customers/{customer_id}/customerLifecycleGoal"

            lifecycle_goal = CustomerLifecycleGoal()
            lifecycle_goal.resource_name = resource_name

            update_fields = []
            value_settings = LifecycleGoalValueSettings()

            if value is not None:
                value_settings.value = value
                update_fields.append("customer_acquisition_goal_value_settings.value")
            if high_lifetime_value is not None:
                value_settings.high_lifetime_value = high_lifetime_value
                update_fields.append(
                    "customer_acquisition_goal_value_settings.high_lifetime_value"
                )

            if update_fields:
                lifecycle_goal.customer_acquisition_goal_value_settings = value_settings

            operation = CustomerLifecycleGoalOperation()
            operation.update = lifecycle_goal
            operation.update_mask = field_mask_pb2.FieldMask(paths=update_fields)

            request = ConfigureCustomerLifecycleGoalsRequest()
            request.customer_id = customer_id
            request.operation = operation
            request.validate_only = validate_only

            response: ConfigureCustomerLifecycleGoalsResponse = (
                self.client.configure_customer_lifecycle_goals(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Updated customer lifecycle goal for customer {customer_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to update customer lifecycle goal: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e


def create_customer_lifecycle_goal_tools(
    service: CustomerLifecycleGoalService,
) -> List[Callable[..., Awaitable[Any]]]:
    """Create tool functions for the customer lifecycle goal service."""
    tools = []

    async def create_customer_lifecycle_goal(
        ctx: Context,
        *,
        customer_id: Optional[str] = None,
        value: Optional[float] = None,
        high_lifetime_value: Optional[float] = None,
        validate_only: bool = False,
    ) -> Dict[str, Any]:
        """Create account-level customer lifecycle goal value settings.

        Sets default customer acquisition goal values for the account. Campaigns
        that enable customer acquisition optimization inherit these values unless
        they override them with campaign-level lifecycle goal settings.

        Args:
            customer_id: The customer ID
            value: Incremental conversion value for new non-high-value customers
            high_lifetime_value: Incremental conversion value for new high-value customers
                (must be greater than value if both are set)
            validate_only: If true, only validates without executing

        Returns:
            Configuration result details

        Example:
            result = await create_customer_lifecycle_goal(
                customer_id="1234567890",
                value=5.0,
                high_lifetime_value=25.0
            )
        """
        return await service.create_customer_lifecycle_goal(
            ctx=ctx,
            customer_id=customer_id,
            value=value,
            high_lifetime_value=high_lifetime_value,
            validate_only=validate_only,
        )

    async def update_customer_lifecycle_goal(
        ctx: Context,
        *,
        customer_id: Optional[str] = None,
        value: Optional[float] = None,
        high_lifetime_value: Optional[float] = None,
        validate_only: bool = False,
    ) -> Dict[str, Any]:
        """Update account-level customer lifecycle goal value settings.

        Args:
            customer_id: The customer ID
            value: New incremental conversion value for new non-high-value customers
            high_lifetime_value: New incremental conversion value for high-value customers
                (must be greater than value if both are set)
            validate_only: If true, only validates without executing

        Returns:
            Configuration result details

        Example:
            result = await update_customer_lifecycle_goal(
                customer_id="1234567890",
                value=7.5,
                high_lifetime_value=30.0
            )
        """
        return await service.update_customer_lifecycle_goal(
            ctx=ctx,
            customer_id=customer_id,
            value=value,
            high_lifetime_value=high_lifetime_value,
            validate_only=validate_only,
        )

    tools.extend([create_customer_lifecycle_goal, update_customer_lifecycle_goal])
    return tools


def register_customer_lifecycle_goal_tools(
    mcp: FastMCP[Any],
) -> CustomerLifecycleGoalService:
    """Register customer lifecycle goal tools with the MCP server.

    Returns the service instance for testing purposes.
    """
    service = CustomerLifecycleGoalService()
    tools = create_customer_lifecycle_goal_tools(service)

    for tool in tools:
        mcp.tool(tool)

    return service
