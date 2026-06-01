"""Reach plan service implementation using Google Ads SDK."""

from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastmcp import Context, FastMCP
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.v20.common.types.criteria import GenderInfo
from google.ads.googleads.v20.enums.types.gender_type import GenderTypeEnum
from google.ads.googleads.v20.enums.types.reach_plan_age_range import (
    ReachPlanAgeRangeEnum,
)
from google.ads.googleads.v20.services.services.reach_plan_service import (
    ReachPlanServiceClient,
)
from google.ads.googleads.v20.services.types.reach_plan_service import (
    CampaignDuration,
    GenerateReachForecastRequest,
    GenerateReachForecastResponse,
    ListPlannableLocationsRequest,
    ListPlannableLocationsResponse,
    ListPlannableProductsRequest,
    ListPlannableProductsResponse,
    PlannedProduct,
    Targeting,
)

from src.sdk_client import get_sdk_client
from src.utils import (
    format_ads_error,
    format_customer_id,
    get_logger,
    serialize_proto_message,
)

logger = get_logger(__name__)


class ReachPlanService:
    """Reach plan service for reach planning and forecasting."""

    def __init__(self) -> None:
        """Initialize the reach plan service."""
        self._client: Optional[ReachPlanServiceClient] = None

    @property
    def client(self) -> ReachPlanServiceClient:
        """Get the reach plan service client."""
        if self._client is None:
            sdk_client = get_sdk_client()
            self._client = sdk_client.client.get_service(
                "ReachPlanService", version="v20"
            )
        assert self._client is not None
        return self._client

    async def list_plannable_locations(
        self,
        ctx: Context,
    ) -> Dict[str, Any]:
        """List all plannable locations for reach planning.

        Args:
            ctx: FastMCP context

        Returns:
            List of plannable locations with details
        """
        try:
            # Create request
            request = ListPlannableLocationsRequest()

            # Make the API call
            response: ListPlannableLocationsResponse = (
                self.client.list_plannable_locations(request=request)
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to list plannable locations: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def list_plannable_products(
        self,
        ctx: Context,
        plannable_location_id: str,
    ) -> List[Dict[str, Any]]:
        """List all plannable products for a given location.

        Args:
            ctx: FastMCP context
            plannable_location_id: The plannable location ID

        Returns:
            List of plannable products for the location
        """
        try:
            # Create request
            request = ListPlannableProductsRequest()
            request.plannable_location_id = plannable_location_id

            # Make the API call
            response: ListPlannableProductsResponse = (
                self.client.list_plannable_products(request=request)
            )

            # Process results
            products = []
            for product in response.product_metadata:
                product_dict = {
                    "plannable_product_code": product.plannable_product_code,
                    "plannable_product_name": product.plannable_product_name,
                    "plannable_targeting": {
                        "age_ranges": [
                            str(age_range)
                            for age_range in product.plannable_targeting.age_ranges
                        ]
                        if product.plannable_targeting
                        and product.plannable_targeting.age_ranges
                        else [],
                        "genders": [
                            str(gender)
                            for gender in product.plannable_targeting.genders
                        ]
                        if product.plannable_targeting
                        and product.plannable_targeting.genders
                        else [],
                        "devices": [
                            str(device)
                            for device in product.plannable_targeting.devices
                        ]
                        if product.plannable_targeting
                        and product.plannable_targeting.devices
                        else [],
                        "networks": [
                            str(network)
                            for network in product.plannable_targeting.networks
                        ]
                        if product.plannable_targeting
                        and product.plannable_targeting.networks
                        else [],
                    },
                }
                products.append(product_dict)

            await ctx.log(
                level="info",
                message=f"Found {len(products)} plannable products for location {plannable_location_id}",
            )

            return products

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to list plannable products: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def generate_reach_forecast(
        self,
        ctx: Context,
        customer_id: str,
        plannable_location_id: str,
        planned_products: List[Dict[str, Any]],
        duration_days: int = 30,
        currency_code: str = "USD",
        min_effective_frequency: int = 1,
        age_range: Optional[str] = None,
        genders: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Generate a reach forecast for a media plan.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            plannable_location_id: Location ID from list_plannable_locations
            planned_products: List of products to forecast, each with:
                - plannable_product_code: Product code from list_plannable_products
                - budget_micros: Budget in micros (e.g. 1_000_000_000 = $1000)
            duration_days: Campaign duration in days (1–92)
            currency_code: ISO 4217 currency code (e.g. "USD", "EUR")
            min_effective_frequency: Minimum ad exposures per user to count as reached (1–10)
            age_range: Optional age range (e.g. "AGE_RANGE_18_34", "AGE_RANGE_25_54")
            genders: Optional genders to target (e.g. ["MALE", "FEMALE"])

        Returns:
            Reach forecast with on_target_reach, total_reach, on_target_impressions,
            total_impressions, and viewable_impressions per planned product.
        """
        try:
            customer_id = format_customer_id(customer_id)

            # Build campaign duration
            campaign_duration = CampaignDuration()
            campaign_duration.duration_in_days = duration_days

            # Build targeting
            targeting = Targeting()
            targeting.plannable_location_ids.append(plannable_location_id)

            if age_range:
                targeting.age_range = getattr(
                    ReachPlanAgeRangeEnum.ReachPlanAgeRange, age_range
                )

            if genders:
                for gender_str in genders:
                    gender_info = GenderInfo()
                    gender_info.type_ = getattr(GenderTypeEnum.GenderType, gender_str)
                    targeting.genders.append(gender_info)

            # Build planned products
            products = []
            for prod in planned_products:
                planned_product = PlannedProduct()
                planned_product.plannable_product_code = prod["plannable_product_code"]
                planned_product.budget_micros = prod["budget_micros"]
                products.append(planned_product)

            # Build request
            request = GenerateReachForecastRequest()
            request.customer_id = customer_id
            request.currency_code = currency_code
            request.campaign_duration = campaign_duration
            request.targeting = targeting
            request.planned_products = products
            request.min_effective_frequency = min_effective_frequency

            response: GenerateReachForecastResponse = (
                self.client.generate_reach_forecast(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Generated reach forecast for {len(products)} product(s) in location {plannable_location_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to generate reach forecast: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e


def create_reach_plan_tools(
    service: ReachPlanService,
) -> List[Callable[..., Awaitable[Any]]]:
    """Create tool functions for the reach plan service.

    This returns a list of tool functions that can be registered with FastMCP.
    This approach makes the tools testable by allowing service injection.
    """
    tools = []

    async def list_plannable_locations(
        ctx: Context,
    ) -> Dict[str, Any]:
        """List all available plannable locations for reach planning.

        Returns:
            Response containing plannable locations with ID, name, country code, and location type
        """
        return await service.list_plannable_locations(ctx=ctx)

    async def list_plannable_products(
        ctx: Context,
        plannable_location_id: str,
    ) -> List[Dict[str, Any]]:
        """List all plannable products available for a specific location.

        Args:
            plannable_location_id: The plannable location ID to get products for

        Returns:
            List of plannable products with codes, names, and targeting options
        """
        return await service.list_plannable_products(
            ctx=ctx,
            plannable_location_id=plannable_location_id,
        )

    async def generate_reach_forecast(
        ctx: Context,
        customer_id: str,
        plannable_location_id: str,
        planned_products: List[Dict[str, Any]],
        duration_days: int = 30,
        currency_code: str = "USD",
        min_effective_frequency: int = 1,
        age_range: Optional[str] = None,
        genders: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Generate a reach forecast for a YouTube/video media plan.

        Use list_plannable_locations to get plannable_location_id and
        list_plannable_products to get available plannable_product_codes.

        Args:
            customer_id: The customer ID
            plannable_location_id: Location ID (e.g. "2840" for USA)
            planned_products: List of products to include in the forecast, each with:
                - plannable_product_code: Code from list_plannable_products
                  (e.g. "TRUEVIEW_IN_STREAM", "BUMPER", "NON_SKIPPABLE_IN_STREAM")
                - budget_micros: Budget in micros (e.g. 5_000_000_000 = $5000)
            duration_days: Campaign duration in days, max 92 (default 30)
            currency_code: ISO 4217 currency code (default "USD")
            min_effective_frequency: Minimum exposures per user (1–10, default 1)
            age_range: Optional age range filter, e.g.:
                "AGE_RANGE_18_24", "AGE_RANGE_18_34", "AGE_RANGE_25_54",
                "AGE_RANGE_35_65_UP" — see list_plannable_products for supported values
            genders: Optional gender filter: ["MALE"], ["FEMALE"], or ["MALE", "FEMALE"]

        Returns:
            Forecast results including:
            - reach_curve: Array of reach/frequency points across budget levels
            - on_target_reach: Unique users reached within the targeted audience
            - total_reach: Total unique users reached
            - on_target_impressions: Impressions within targeted audience
            - total_impressions: Total impressions
            - viewable_impressions: Viewable impressions

        Example:
            planned_products=[
                {"plannable_product_code": "TRUEVIEW_IN_STREAM", "budget_micros": 5000000000}
            ]
        """
        return await service.generate_reach_forecast(
            ctx=ctx,
            customer_id=customer_id,
            plannable_location_id=plannable_location_id,
            planned_products=planned_products,
            duration_days=duration_days,
            currency_code=currency_code,
            min_effective_frequency=min_effective_frequency,
            age_range=age_range,
            genders=genders,
        )

    tools.extend(
        [
            list_plannable_locations,
            list_plannable_products,
            generate_reach_forecast,
        ]
    )
    return tools


def register_reach_plan_tools(mcp: FastMCP[Any]) -> ReachPlanService:
    """Register reach plan tools with the MCP server.

    Returns the ReachPlanService instance for testing purposes.
    """
    service = ReachPlanService()
    tools = create_reach_plan_tools(service)

    # Register each tool
    for tool in tools:
        mcp.tool(tool)

    return service
