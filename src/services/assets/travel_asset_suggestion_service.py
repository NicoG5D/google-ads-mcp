"""Travel Asset Suggestion service implementation with full v20 type safety."""

from typing import Any, Awaitable, Callable, Dict, List, Optional, Sequence

from fastmcp import Context, FastMCP
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.v20.services.services.travel_asset_suggestion_service import (
    TravelAssetSuggestionServiceClient,
)
from google.ads.googleads.v20.services.types.travel_asset_suggestion_service import (
    SuggestTravelAssetsRequest,
    SuggestTravelAssetsResponse,
)

from src.sdk_client import get_sdk_client
from src.utils import (
    format_ads_error,
    resolve_customer_id,
    get_logger,
    serialize_proto_message,
)

logger = get_logger(__name__)


class TravelAssetSuggestionService:
    """Service for suggesting travel assets (hotel content) in Google Ads.

    Generates asset suggestions for hotel campaigns based on Google Maps
    place data, including headlines, descriptions, and images.
    """

    def __init__(self) -> None:
        self._client: Optional[TravelAssetSuggestionServiceClient] = None

    @property
    def client(self) -> TravelAssetSuggestionServiceClient:
        if self._client is None:
            sdk_client = get_sdk_client()
            self._client = sdk_client.client.get_service(
                "TravelAssetSuggestionService", version="v20"
            )
        assert self._client is not None
        return self._client

    async def suggest_travel_assets(
        self,
        ctx: Context,
        *,
        customer_id: Optional[str] = None,
        language_option: str,
        place_ids: Sequence[str],
    ) -> Dict[str, Any]:
        """Suggest travel assets for hotel campaigns.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            language_option: Language in BCP 47 format (e.g. "en-US", "zh-CN")
            place_ids: Google Maps Place IDs of hotels to get assets for

        Returns:
            Suggested text and image assets for each hotel place ID
        """
        try:
            formatted_customer_id = resolve_customer_id(customer_id)

            request = SuggestTravelAssetsRequest()
            request.customer_id = formatted_customer_id
            request.language_option = language_option
            request.place_ids = list(place_ids)

            response: SuggestTravelAssetsResponse = self.client.suggest_travel_assets(
                request=request
            )

            await ctx.log(
                level="info",
                message=f"Suggested travel assets for customer {formatted_customer_id} "
                f"with {len(place_ids)} place(s) in language '{language_option}'",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to suggest travel assets: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e


def create_travel_asset_suggestion_tools(
    service: TravelAssetSuggestionService,
) -> List[Callable[..., Awaitable[Any]]]:
    """Create tool functions for the travel asset suggestion service."""
    tools = []

    async def suggest_travel_assets(
        ctx: Context,
        *,
        customer_id: Optional[str] = None,
        language_option: str,
        place_ids: List[str],
    ) -> Dict[str, Any]:
        """Suggest text and image assets for hotel travel campaigns.

        Generates ready-to-use asset suggestions for hotel properties based on
        Google Maps Place data. Suggestions include headlines, descriptions,
        images, and a suggested call-to-action for hotel campaigns.

        Args:
            customer_id: The customer ID (with or without hyphens)
            language_option: Language for asset text in BCP 47 format
                (e.g. "en-US", "zh-CN", "fr-FR")
            place_ids: List of Google Maps Place IDs for hotels
                (see https://developers.google.com/places/web-service/place-id)

        Returns:
            Hotel asset suggestions for each place ID including:
            - hotel_name: Name of the hotel
            - final_url: Suggested landing page URL
            - call_to_action: Suggested call-to-action type
            - text_assets: Headline and description suggestions
            - image_assets: Landscape, portrait, and square image suggestions
            - status: Whether suggestions were successfully retrieved

        Example:
            result = await suggest_travel_assets(
                customer_id="1234567890",
                language_option="en-US",
                place_ids=["ChIJN1t_tDeuEmsRUsoyG83frY4", "ChIJP3Sa8ziYEmsRUKgyFmh9AQM"]
            )
        """
        return await service.suggest_travel_assets(
            ctx=ctx,
            customer_id=customer_id,
            language_option=language_option,
            place_ids=place_ids,
        )

    tools.append(suggest_travel_assets)
    return tools


def register_travel_asset_suggestion_tools(
    mcp: FastMCP[Any],
) -> TravelAssetSuggestionService:
    """Register travel asset suggestion tools with the MCP server.

    Returns the service instance for testing purposes.
    """
    service = TravelAssetSuggestionService()
    tools = create_travel_asset_suggestion_tools(service)

    for tool in tools:
        mcp.tool(tool)

    return service
