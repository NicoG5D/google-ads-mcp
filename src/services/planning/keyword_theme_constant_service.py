"""Keyword Theme Constant service implementation with full v20 type safety."""

from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastmcp import Context, FastMCP
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.v20.services.services.keyword_theme_constant_service import (
    KeywordThemeConstantServiceClient,
)
from google.ads.googleads.v20.services.types.keyword_theme_constant_service import (
    SuggestKeywordThemeConstantsRequest,
    SuggestKeywordThemeConstantsResponse,
)

from src.sdk_client import get_sdk_client
from src.utils import (
    format_ads_error,
    get_logger,
    serialize_proto_message,
)

logger = get_logger(__name__)


class KeywordThemeConstantService:
    """Service for suggesting keyword theme constants in Google Ads.

    Keyword theme constants are used for Smart Campaign keyword themes
    that help target relevant searches.
    """

    def __init__(self) -> None:
        self._client: Optional[KeywordThemeConstantServiceClient] = None

    @property
    def client(self) -> KeywordThemeConstantServiceClient:
        if self._client is None:
            sdk_client = get_sdk_client()
            self._client = sdk_client.client.get_service(
                "KeywordThemeConstantService", version="v20"
            )
        assert self._client is not None
        return self._client

    async def suggest_keyword_theme_constants(
        self,
        ctx: Context,
        query_text: str,
        country_code: str = "US",
        language_code: str = "en",
    ) -> Dict[str, Any]:
        """Suggest keyword theme constants for Smart Campaigns.

        Args:
            ctx: FastMCP context
            query_text: The query text to map to keyword themes
            country_code: Upper-case ISO-3166 country code (default: US)
            language_code: Two-letter language code (default: en)

        Returns:
            List of suggested keyword theme constants
        """
        try:
            request = SuggestKeywordThemeConstantsRequest()
            request.query_text = query_text
            request.country_code = country_code
            request.language_code = language_code

            response: SuggestKeywordThemeConstantsResponse = (
                self.client.suggest_keyword_theme_constants(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Suggested keyword themes for query '{query_text}' ({country_code}/{language_code})",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to suggest keyword theme constants: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e


def create_keyword_theme_constant_tools(
    service: KeywordThemeConstantService,
) -> List[Callable[..., Awaitable[Any]]]:
    """Create tool functions for the keyword theme constant service."""
    tools = []

    async def suggest_keyword_theme_constants(
        ctx: Context,
        query_text: str,
        country_code: str = "US",
        language_code: str = "en",
    ) -> Dict[str, Any]:
        """Suggest keyword theme constants for Smart Campaigns.

        Returns keyword theme suggestions that can be used to target relevant
        searches in Smart Campaigns. Keyword themes help Smart Campaigns
        understand what topics and searches the business wants to appear for.

        Args:
            query_text: The keyword or phrase to find matching themes for
                (e.g. "plumber" or "roofer")
            country_code: Upper-case ISO-3166 two-letter country code to refine
                the scope of the query (default: US)
            language_code: Two-letter language code to refine the scope of the
                query (default: en)

        Returns:
            List of suggested keyword theme constants with resource names and display names

        Example:
            result = await suggest_keyword_theme_constants(
                query_text="plumber",
                country_code="US",
                language_code="en"
            )
        """
        return await service.suggest_keyword_theme_constants(
            ctx=ctx,
            query_text=query_text,
            country_code=country_code,
            language_code=language_code,
        )

    tools.append(suggest_keyword_theme_constants)
    return tools


def register_keyword_theme_constant_tools(
    mcp: FastMCP[Any],
) -> KeywordThemeConstantService:
    """Register keyword theme constant tools with the MCP server.

    Returns the service instance for testing purposes.
    """
    service = KeywordThemeConstantService()
    tools = create_keyword_theme_constant_tools(service)

    for tool in tools:
        mcp.tool(tool)

    return service
