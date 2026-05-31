"""Campaign Lifecycle Goal service implementation with full v20 type safety."""

from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastmcp import Context, FastMCP
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.v20.common.types.lifecycle_goals import (
    LifecycleGoalValueSettings,
)
from google.ads.googleads.v20.enums.types.customer_acquisition_optimization_mode import (
    CustomerAcquisitionOptimizationModeEnum,
)
from google.ads.googleads.v20.resources.types.campaign_lifecycle_goal import (
    CampaignLifecycleGoal,
    CustomerAcquisitionGoalSettings,
)
from google.ads.googleads.v20.services.services.campaign_lifecycle_goal_service import (
    CampaignLifecycleGoalServiceClient,
)
from google.ads.googleads.v20.services.types.campaign_lifecycle_goal_service import (
    CampaignLifecycleGoalOperation,
    ConfigureCampaignLifecycleGoalsRequest,
    ConfigureCampaignLifecycleGoalsResponse,
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


class CampaignLifecycleGoalService:
    """Service for configuring campaign lifecycle goals in Google Ads.

    Campaign lifecycle goals allow you to optimize campaigns for customer
    acquisition objectives, controlling how bidding treats new vs existing customers.
    """

    def __init__(self) -> None:
        self._client: Optional[CampaignLifecycleGoalServiceClient] = None

    @property
    def client(self) -> CampaignLifecycleGoalServiceClient:
        if self._client is None:
            sdk_client = get_sdk_client()
            self._client = sdk_client.client.get_service(
                "CampaignLifecycleGoalService", version="v20"
            )
        assert self._client is not None
        return self._client

    async def create_campaign_lifecycle_goal(
        self,
        ctx: Context,
        customer_id: str,
        campaign_id: str,
        optimization_mode: CustomerAcquisitionOptimizationModeEnum.CustomerAcquisitionOptimizationMode,
        value: Optional[float] = None,
        high_lifetime_value: Optional[float] = None,
        validate_only: bool = False,
    ) -> Dict[str, Any]:
        """Create a campaign lifecycle goal for customer acquisition optimization.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            campaign_id: The campaign ID to attach lifecycle goal to
            optimization_mode: How the campaign optimizes for customer acquisition
            value: Incremental conversion value for new non-high-value customers
            high_lifetime_value: Incremental conversion value for new high-value customers
            validate_only: If true, only validates without executing

        Returns:
            Configuration result details
        """
        try:
            customer_id = format_customer_id(customer_id)
            campaign_resource = f"customers/{customer_id}/campaigns/{campaign_id}"
            resource_name = f"customers/{customer_id}/campaignLifecycleGoal/{campaign_id}"

            goal_settings = CustomerAcquisitionGoalSettings()
            goal_settings.optimization_mode = optimization_mode

            if value is not None or high_lifetime_value is not None:
                value_settings = LifecycleGoalValueSettings()
                if value is not None:
                    value_settings.value = value
                if high_lifetime_value is not None:
                    value_settings.high_lifetime_value = high_lifetime_value
                goal_settings.value_settings = value_settings

            lifecycle_goal = CampaignLifecycleGoal()
            lifecycle_goal.resource_name = resource_name
            lifecycle_goal.campaign = campaign_resource
            lifecycle_goal.customer_acquisition_goal_settings = goal_settings

            operation = CampaignLifecycleGoalOperation()
            operation.create = lifecycle_goal

            request = ConfigureCampaignLifecycleGoalsRequest()
            request.customer_id = customer_id
            request.operation = operation
            request.validate_only = validate_only

            response: ConfigureCampaignLifecycleGoalsResponse = (
                self.client.configure_campaign_lifecycle_goals(request=request)
            )

            await ctx.log(
                level="info",
                message=(
                    f"Created campaign lifecycle goal for campaign {campaign_id}, "
                    f"optimization_mode={optimization_mode}"
                ),
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to create campaign lifecycle goal: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def update_campaign_lifecycle_goal(
        self,
        ctx: Context,
        customer_id: str,
        campaign_id: str,
        optimization_mode: Optional[
            CustomerAcquisitionOptimizationModeEnum.CustomerAcquisitionOptimizationMode
        ] = None,
        value: Optional[float] = None,
        high_lifetime_value: Optional[float] = None,
        validate_only: bool = False,
    ) -> Dict[str, Any]:
        """Update an existing campaign lifecycle goal.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            campaign_id: The campaign ID whose lifecycle goal to update
            optimization_mode: New optimization mode for customer acquisition
            value: New incremental conversion value for new non-high-value customers
            high_lifetime_value: New incremental conversion value for high-value customers
            validate_only: If true, only validates without executing

        Returns:
            Configuration result details
        """
        try:
            customer_id = format_customer_id(customer_id)
            resource_name = f"customers/{customer_id}/campaignLifecycleGoal/{campaign_id}"

            lifecycle_goal = CampaignLifecycleGoal()
            lifecycle_goal.resource_name = resource_name

            update_fields = []

            if optimization_mode is not None:
                goal_settings = CustomerAcquisitionGoalSettings()
                goal_settings.optimization_mode = optimization_mode
                update_fields.append(
                    "customer_acquisition_goal_settings.optimization_mode"
                )

                if value is not None or high_lifetime_value is not None:
                    value_settings = LifecycleGoalValueSettings()
                    if value is not None:
                        value_settings.value = value
                        update_fields.append(
                            "customer_acquisition_goal_settings.value_settings.value"
                        )
                    if high_lifetime_value is not None:
                        value_settings.high_lifetime_value = high_lifetime_value
                        update_fields.append(
                            "customer_acquisition_goal_settings.value_settings.high_lifetime_value"
                        )
                    goal_settings.value_settings = value_settings

                lifecycle_goal.customer_acquisition_goal_settings = goal_settings
            elif value is not None or high_lifetime_value is not None:
                goal_settings = CustomerAcquisitionGoalSettings()
                value_settings = LifecycleGoalValueSettings()
                if value is not None:
                    value_settings.value = value
                    update_fields.append(
                        "customer_acquisition_goal_settings.value_settings.value"
                    )
                if high_lifetime_value is not None:
                    value_settings.high_lifetime_value = high_lifetime_value
                    update_fields.append(
                        "customer_acquisition_goal_settings.value_settings.high_lifetime_value"
                    )
                goal_settings.value_settings = value_settings
                lifecycle_goal.customer_acquisition_goal_settings = goal_settings

            operation = CampaignLifecycleGoalOperation()
            operation.update = lifecycle_goal
            operation.update_mask = field_mask_pb2.FieldMask(paths=update_fields)

            request = ConfigureCampaignLifecycleGoalsRequest()
            request.customer_id = customer_id
            request.operation = operation
            request.validate_only = validate_only

            response: ConfigureCampaignLifecycleGoalsResponse = (
                self.client.configure_campaign_lifecycle_goals(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Updated campaign lifecycle goal for campaign {campaign_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to update campaign lifecycle goal: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e


def create_campaign_lifecycle_goal_tools(
    service: CampaignLifecycleGoalService,
) -> List[Callable[..., Awaitable[Any]]]:
    """Create tool functions for the campaign lifecycle goal service."""
    tools = []

    async def create_campaign_lifecycle_goal(
        ctx: Context,
        customer_id: str,
        campaign_id: str,
        optimization_mode: str,
        value: Optional[float] = None,
        high_lifetime_value: Optional[float] = None,
        validate_only: bool = False,
    ) -> Dict[str, Any]:
        """Create a campaign lifecycle goal for customer acquisition optimization.

        Configure how this campaign treats new versus existing customers when
        bidding. Supports customer acquisition goal optimization modes.

        Args:
            customer_id: The customer ID
            campaign_id: The campaign ID to attach lifecycle goal to
            optimization_mode: Optimization mode - UNSPECIFIED, UNKNOWN, DISABLED,
                BID_HIGHER_FOR_NEW_CUSTOMER, or TARGET_ALL_EQUALLY
            value: Incremental conversion value for new non-high-value customers
            high_lifetime_value: Incremental conversion value for new high-value customers
            validate_only: If true, only validates without executing

        Returns:
            Configuration result details

        Example:
            result = await create_campaign_lifecycle_goal(
                customer_id="1234567890",
                campaign_id="9876543210",
                optimization_mode="BID_HIGHER_FOR_NEW_CUSTOMER",
                value=5.0,
                high_lifetime_value=20.0
            )
        """
        mode_enum = resolve_enum(
            CustomerAcquisitionOptimizationModeEnum.CustomerAcquisitionOptimizationMode,
            optimization_mode,
            "optimization_mode",
        )
        return await service.create_campaign_lifecycle_goal(
            ctx=ctx,
            customer_id=customer_id,
            campaign_id=campaign_id,
            optimization_mode=mode_enum,
            value=value,
            high_lifetime_value=high_lifetime_value,
            validate_only=validate_only,
        )

    async def update_campaign_lifecycle_goal(
        ctx: Context,
        customer_id: str,
        campaign_id: str,
        optimization_mode: Optional[str] = None,
        value: Optional[float] = None,
        high_lifetime_value: Optional[float] = None,
        validate_only: bool = False,
    ) -> Dict[str, Any]:
        """Update an existing campaign lifecycle goal.

        Args:
            customer_id: The customer ID
            campaign_id: The campaign ID whose lifecycle goal to update
            optimization_mode: New optimization mode - UNSPECIFIED, UNKNOWN, DISABLED,
                BID_HIGHER_FOR_NEW_CUSTOMER, or TARGET_ALL_EQUALLY
            value: New incremental conversion value for new non-high-value customers
            high_lifetime_value: New incremental conversion value for high-value customers
            validate_only: If true, only validates without executing

        Returns:
            Configuration result details

        Example:
            result = await update_campaign_lifecycle_goal(
                customer_id="1234567890",
                campaign_id="9876543210",
                optimization_mode="TARGET_ALL_EQUALLY"
            )
        """
        mode_enum: Optional[
            CustomerAcquisitionOptimizationModeEnum.CustomerAcquisitionOptimizationMode
        ] = None
        if optimization_mode is not None:
            mode_enum = resolve_enum(
                CustomerAcquisitionOptimizationModeEnum.CustomerAcquisitionOptimizationMode,
                optimization_mode,
                "optimization_mode",
            )
        return await service.update_campaign_lifecycle_goal(
            ctx=ctx,
            customer_id=customer_id,
            campaign_id=campaign_id,
            optimization_mode=mode_enum,
            value=value,
            high_lifetime_value=high_lifetime_value,
            validate_only=validate_only,
        )

    tools.extend([create_campaign_lifecycle_goal, update_campaign_lifecycle_goal])
    return tools


def register_campaign_lifecycle_goal_tools(
    mcp: FastMCP[Any],
) -> CampaignLifecycleGoalService:
    """Register campaign lifecycle goal tools with the MCP server.

    Returns the service instance for testing purposes.
    """
    service = CampaignLifecycleGoalService()
    tools = create_campaign_lifecycle_goal_tools(service)

    for tool in tools:
        mcp.tool(tool)

    return service
