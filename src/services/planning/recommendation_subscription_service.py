"""Recommendation Subscription service implementation with full v20 type safety."""

from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastmcp import Context, FastMCP
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.v20.enums.types.recommendation_subscription_status import (
    RecommendationSubscriptionStatusEnum,
)
from google.ads.googleads.v20.enums.types.recommendation_type import (
    RecommendationTypeEnum,
)
from google.ads.googleads.v20.enums.types.response_content_type import (
    ResponseContentTypeEnum,
)
from google.ads.googleads.v20.resources.types.recommendation_subscription import (
    RecommendationSubscription,
)
from google.ads.googleads.v20.services.services.recommendation_subscription_service import (
    RecommendationSubscriptionServiceClient,
)
from google.ads.googleads.v20.services.types.recommendation_subscription_service import (
    MutateRecommendationSubscriptionRequest,
    MutateRecommendationSubscriptionResponse,
    RecommendationSubscriptionOperation,
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


class RecommendationSubscriptionService:
    """Service for managing recommendation subscriptions in Google Ads.

    Recommendation subscriptions allow customers to opt into automatic
    application of certain recommendation types.
    """

    def __init__(self) -> None:
        self._client: Optional[RecommendationSubscriptionServiceClient] = None

    @property
    def client(self) -> RecommendationSubscriptionServiceClient:
        if self._client is None:
            sdk_client = get_sdk_client()
            self._client = sdk_client.client.get_service(
                "RecommendationSubscriptionService", version="v20"
            )
        assert self._client is not None
        return self._client

    async def create_recommendation_subscription(
        self,
        ctx: Context,
        *,
        customer_id: Optional[str] = None,
        recommendation_type: RecommendationTypeEnum.RecommendationType,
        status: RecommendationSubscriptionStatusEnum.RecommendationSubscriptionStatus,
        partial_failure: bool = False,
        validate_only: bool = False,
        response_content_type: ResponseContentTypeEnum.ResponseContentType = ResponseContentTypeEnum.ResponseContentType.MUTABLE_RESOURCE,
    ) -> Dict[str, Any]:
        """Create a new recommendation subscription.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            recommendation_type: The type of recommendation to subscribe to
            status: The subscription status (ENABLED or PAUSED)
            partial_failure: If true, valid operations succeed even if others fail
            validate_only: If true, only validates without executing
            response_content_type: What to return in response

        Returns:
            Created recommendation subscription details
        """
        try:
            customer_id = resolve_customer_id(customer_id)

            subscription = RecommendationSubscription()
            subscription.type_ = recommendation_type
            subscription.status = status

            operation = RecommendationSubscriptionOperation()
            operation.create = subscription

            request = MutateRecommendationSubscriptionRequest()
            request.customer_id = customer_id
            request.operations = [operation]
            request.partial_failure = partial_failure
            request.validate_only = validate_only
            request.response_content_type = response_content_type

            response: MutateRecommendationSubscriptionResponse = (
                self.client.mutate_recommendation_subscription(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Created recommendation subscription for type {recommendation_type} for customer {customer_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to create recommendation subscription: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def update_recommendation_subscription(
        self,
        ctx: Context,
        *,
        customer_id: Optional[str] = None,
        recommendation_type: str,
        status: RecommendationSubscriptionStatusEnum.RecommendationSubscriptionStatus,
        partial_failure: bool = False,
        validate_only: bool = False,
        response_content_type: ResponseContentTypeEnum.ResponseContentType = ResponseContentTypeEnum.ResponseContentType.MUTABLE_RESOURCE,
    ) -> Dict[str, Any]:
        """Update an existing recommendation subscription.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            recommendation_type: The recommendation type identifying the subscription
            status: New subscription status (ENABLED or PAUSED)
            partial_failure: If true, valid operations succeed even if others fail
            validate_only: If true, only validates without executing
            response_content_type: What to return in response

        Returns:
            Updated recommendation subscription details
        """
        try:
            customer_id = resolve_customer_id(customer_id)
            resource_name = f"customers/{customer_id}/recommendationSubscriptions/{recommendation_type}"

            subscription = RecommendationSubscription()
            subscription.resource_name = resource_name
            subscription.status = status

            operation = RecommendationSubscriptionOperation()
            operation.update = subscription
            operation.update_mask = field_mask_pb2.FieldMask(paths=["status"])

            request = MutateRecommendationSubscriptionRequest()
            request.customer_id = customer_id
            request.operations = [operation]
            request.partial_failure = partial_failure
            request.validate_only = validate_only
            request.response_content_type = response_content_type

            response: MutateRecommendationSubscriptionResponse = (
                self.client.mutate_recommendation_subscription(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Updated recommendation subscription {recommendation_type} for customer {customer_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to update recommendation subscription: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e


def create_recommendation_subscription_tools(
    service: RecommendationSubscriptionService,
) -> List[Callable[..., Awaitable[Any]]]:
    """Create tool functions for the recommendation subscription service."""
    tools = []

    async def create_recommendation_subscription(
        ctx: Context,
        *,
        customer_id: Optional[str] = None,
        recommendation_type: str,
        status: str = "ENABLED",
        partial_failure: bool = False,
        validate_only: bool = False,
    ) -> Dict[str, Any]:
        """Subscribe to automatic application of a recommendation type.

        Recommendation subscriptions allow Google Ads to automatically apply
        certain recommendation types to a customer account, reducing manual
        optimization effort.

        Args:
            customer_id: The customer ID
            recommendation_type: The recommendation type to subscribe to
                (e.g. KEYWORD, TARGET_CPA_OPT_IN, MAXIMIZE_CONVERSIONS_OPT_IN)
            status: Subscription status - ENABLED or PAUSED (default: ENABLED)
            partial_failure: If true, valid operations succeed even if others fail
            validate_only: If true, only validates without executing

        Returns:
            Created recommendation subscription details

        Example:
            result = await create_recommendation_subscription(
                customer_id="1234567890",
                recommendation_type="KEYWORD",
                status="ENABLED"
            )
        """
        type_enum = resolve_enum(
            RecommendationTypeEnum.RecommendationType,
            recommendation_type,
            "recommendation_type",
        )
        status_enum = resolve_enum(
            RecommendationSubscriptionStatusEnum.RecommendationSubscriptionStatus,
            status,
            "status",
        )
        return await service.create_recommendation_subscription(
            ctx=ctx,
            customer_id=customer_id,
            recommendation_type=type_enum,
            status=status_enum,
            partial_failure=partial_failure,
            validate_only=validate_only,
        )

    async def update_recommendation_subscription(
        ctx: Context,
        *,
        customer_id: Optional[str] = None,
        recommendation_type: str,
        status: str,
        partial_failure: bool = False,
        validate_only: bool = False,
    ) -> Dict[str, Any]:
        """Update the status of a recommendation subscription.

        Args:
            customer_id: The customer ID
            recommendation_type: The recommendation type identifying the subscription
                (e.g. KEYWORD, TARGET_CPA_OPT_IN)
            status: New subscription status - ENABLED or PAUSED
            partial_failure: If true, valid operations succeed even if others fail
            validate_only: If true, only validates without executing

        Returns:
            Updated recommendation subscription details

        Example:
            result = await update_recommendation_subscription(
                customer_id="1234567890",
                recommendation_type="KEYWORD",
                status="PAUSED"
            )
        """
        status_enum = resolve_enum(
            RecommendationSubscriptionStatusEnum.RecommendationSubscriptionStatus,
            status,
            "status",
        )
        return await service.update_recommendation_subscription(
            ctx=ctx,
            customer_id=customer_id,
            recommendation_type=recommendation_type,
            status=status_enum,
            partial_failure=partial_failure,
            validate_only=validate_only,
        )

    tools.extend(
        [create_recommendation_subscription, update_recommendation_subscription]
    )
    return tools


def register_recommendation_subscription_tools(
    mcp: FastMCP[Any],
) -> RecommendationSubscriptionService:
    """Register recommendation subscription tools with the MCP server.

    Returns the service instance for testing purposes.
    """
    service = RecommendationSubscriptionService()
    tools = create_recommendation_subscription_tools(service)

    for tool in tools:
        mcp.tool(tool)

    return service
