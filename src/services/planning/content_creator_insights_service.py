"""Content Creator Insights service implementation with full v20 type safety."""

from typing import Any, Awaitable, Callable, Dict, List, Optional, Sequence

from fastmcp import Context, FastMCP
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.v20.common.types.criteria import (
    LocationInfo,
    YouTubeChannelInfo,
)
from google.ads.googleads.v20.services.services.content_creator_insights_service import (
    ContentCreatorInsightsServiceClient,
)
from google.ads.googleads.v20.services.types.content_creator_insights_service import (
    GenerateCreatorInsightsRequest,
    GenerateCreatorInsightsResponse,
    GenerateTrendingInsightsRequest,
    GenerateTrendingInsightsResponse,
    SearchAudience,
    SearchTopics,
)

from src.sdk_client import get_sdk_client
from src.utils import (
    format_ads_error,
    format_customer_id,
    get_logger,
    serialize_proto_message,
)

logger = get_logger(__name__)


class ContentCreatorInsightsService:
    """Service for generating content creator insights in Google Ads.

    Provides insights about YouTube creators and trending content
    to help advertisers identify partnership opportunities and understand
    audience trends.
    """

    def __init__(self) -> None:
        self._client: Optional[ContentCreatorInsightsServiceClient] = None

    @property
    def client(self) -> ContentCreatorInsightsServiceClient:
        if self._client is None:
            sdk_client = get_sdk_client()
            self._client = sdk_client.client.get_service(
                "ContentCreatorInsightsService", version="v20"
            )
        assert self._client is not None
        return self._client

    async def generate_creator_insights_by_channels(
        self,
        ctx: Context,
        customer_id: str,
        customer_insights_group: str,
        country_geo_target_constants: Sequence[str],
        youtube_channel_ids: Sequence[str],
    ) -> Dict[str, Any]:
        """Generate creator insights for specific YouTube channels.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            customer_insights_group: User-defined name for the planning group
            country_geo_target_constants: List of country geo target constant
                resource names (e.g. "geoTargetConstants/2840" for USA)
            youtube_channel_ids: List of YouTube channel IDs

        Returns:
            Creator insights for the specified YouTube channels
        """
        try:
            formatted_customer_id = format_customer_id(customer_id)

            country_locations: List[LocationInfo] = []
            for geo_constant in country_geo_target_constants:
                loc = LocationInfo()
                loc.geo_target_constant = geo_constant
                country_locations.append(loc)

            yt_channels: List[YouTubeChannelInfo] = []
            for channel_id in youtube_channel_ids:
                ch = YouTubeChannelInfo()
                ch.channel_id = channel_id
                yt_channels.append(ch)

            search_channels = GenerateCreatorInsightsRequest.YouTubeChannels()
            search_channels.youtube_channels = yt_channels

            request = GenerateCreatorInsightsRequest()
            request.customer_id = formatted_customer_id
            request.customer_insights_group = customer_insights_group
            request.country_locations = country_locations
            request.search_channels = search_channels

            response: GenerateCreatorInsightsResponse = (
                self.client.generate_creator_insights(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Generated creator insights for customer {formatted_customer_id} "
                f"with {len(youtube_channel_ids)} channel(s)",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to generate creator insights: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def generate_trending_insights(
        self,
        ctx: Context,
        customer_id: str,
        customer_insights_group: str,
        country_geo_target_constant: str,
        topic_entity_ids: Optional[Sequence[str]] = None,
    ) -> Dict[str, Any]:
        """Generate trending content insights for a country.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            customer_insights_group: User-defined name for the planning group
            country_geo_target_constant: Country geo target constant resource
                name (e.g. "geoTargetConstants/2840" for USA)
            topic_entity_ids: Optional list of Knowledge Graph entity IDs to
                retrieve trend information for. When not provided, returns
                general trending content.

        Returns:
            Trending content insights for the given country and criteria
        """
        try:
            formatted_customer_id = format_customer_id(customer_id)

            country_location = LocationInfo()
            country_location.geo_target_constant = country_geo_target_constant

            request = GenerateTrendingInsightsRequest()
            request.customer_id = formatted_customer_id
            request.customer_insights_group = customer_insights_group
            request.country_location = country_location

            if topic_entity_ids is not None:
                from google.ads.googleads.v20.common.types.audience_insights_attribute import (
                    AudienceInsightsEntity,
                )

                entities: List[AudienceInsightsEntity] = []
                for entity_id in topic_entity_ids:
                    entity = AudienceInsightsEntity()
                    entity.knowledge_graph_machine_id = entity_id
                    entities.append(entity)
                search_topics = SearchTopics()
                search_topics.entities = entities
                request.search_topics = search_topics

            response: GenerateTrendingInsightsResponse = (
                self.client.generate_trending_insights(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Generated trending insights for customer {formatted_customer_id} "
                f"in country {country_geo_target_constant}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to generate trending insights: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e


def create_content_creator_insights_tools(
    service: ContentCreatorInsightsService,
) -> List[Callable[..., Awaitable[Any]]]:
    """Create tool functions for the content creator insights service."""
    tools = []

    async def generate_creator_insights_by_channels(
        ctx: Context,
        customer_id: str,
        customer_insights_group: str,
        country_geo_target_constants: List[str],
        youtube_channel_ids: List[str],
    ) -> Dict[str, Any]:
        """Generate creator insights for specific YouTube channels.

        Returns detailed insights about YouTube creators including subscriber
        count, view metrics, engagement rates, audience demographics, and
        BrandConnect eligibility.

        Args:
            customer_id: The customer ID (with or without hyphens)
            customer_insights_group: A user-defined name for planning purposes
            country_geo_target_constants: List of country geo target constant
                resource names (e.g. ["geoTargetConstants/2840"] for USA)
            youtube_channel_ids: List of YouTube channel IDs to fetch insights for

        Returns:
            Creator insights including channel metrics, audience attributes,
            and content attributes for each channel

        Example:
            result = await generate_creator_insights_by_channels(
                customer_id="1234567890",
                customer_insights_group="my-planning-group",
                country_geo_target_constants=["geoTargetConstants/2840"],
                youtube_channel_ids=["UCxxxxxx", "UCyyyyyy"]
            )
        """
        return await service.generate_creator_insights_by_channels(
            ctx=ctx,
            customer_id=customer_id,
            customer_insights_group=customer_insights_group,
            country_geo_target_constants=country_geo_target_constants,
            youtube_channel_ids=youtube_channel_ids,
        )

    async def generate_trending_insights(
        ctx: Context,
        customer_id: str,
        customer_insights_group: str,
        country_geo_target_constant: str,
        topic_entity_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Generate trending content insights for a specific country.

        Returns trend direction (RISING or DECLINING) and view metrics for
        content topics in a given country. Useful for discovering trending
        YouTube content relevant to your audience.

        Args:
            customer_id: The customer ID (with or without hyphens)
            customer_insights_group: A user-defined name for planning purposes
            country_geo_target_constant: Country geo target constant resource
                name (e.g. "geoTargetConstants/2840" for USA)
            topic_entity_ids: Optional list of Knowledge Graph entity IDs to
                get trend data for specific topics. When None, returns general
                trending content.

        Returns:
            List of trend insights with trend direction and metrics for the
            latest available month

        Example:
            result = await generate_trending_insights(
                customer_id="1234567890",
                customer_insights_group="my-planning-group",
                country_geo_target_constant="geoTargetConstants/2840",
                topic_entity_ids=["/m/01234", "/m/05678"]
            )
        """
        return await service.generate_trending_insights(
            ctx=ctx,
            customer_id=customer_id,
            customer_insights_group=customer_insights_group,
            country_geo_target_constant=country_geo_target_constant,
            topic_entity_ids=topic_entity_ids,
        )

    tools.append(generate_creator_insights_by_channels)
    tools.append(generate_trending_insights)
    return tools


def register_content_creator_insights_tools(
    mcp: FastMCP[Any],
) -> ContentCreatorInsightsService:
    """Register content creator insights tools with the MCP server.

    Returns the service instance for testing purposes.
    """
    service = ContentCreatorInsightsService()
    tools = create_content_creator_insights_tools(service)

    for tool in tools:
        mcp.tool(tool)

    return service
