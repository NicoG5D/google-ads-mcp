"""User interest service for querying Google's predefined affinity and in-market audiences."""

from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastmcp import Context, FastMCP
from google.ads.googleads.v20.enums.types.user_interest_taxonomy_type import (
    UserInterestTaxonomyTypeEnum,
)
from google.ads.googleads.v20.services.services.google_ads_service import (
    GoogleAdsServiceClient,
)

from src.sdk_client import get_sdk_client
from src.utils import (
    format_customer_id,
    get_logger,
)

logger = get_logger(__name__)

_TAXONOMY_TYPE_MAP = {
    "AFFINITY": UserInterestTaxonomyTypeEnum.UserInterestTaxonomyType.AFFINITY,
    "IN_MARKET": UserInterestTaxonomyTypeEnum.UserInterestTaxonomyType.IN_MARKET,
    "MOBILE_APP_INSTALL_USER": UserInterestTaxonomyTypeEnum.UserInterestTaxonomyType.MOBILE_APP_INSTALL_USER,
    "VERTICAL_GEO": UserInterestTaxonomyTypeEnum.UserInterestTaxonomyType.VERTICAL_GEO,
    "NEW_SMART_PHONE_USER": UserInterestTaxonomyTypeEnum.UserInterestTaxonomyType.NEW_SMART_PHONE_USER,
}

_BASE_QUERY = """
    SELECT
        user_interest.user_interest_id,
        user_interest.name,
        user_interest.taxonomy_type,
        user_interest.user_interest_parent,
        user_interest.launched_to_all,
        user_interest.resource_name
    FROM user_interest
"""


class UserInterestService:
    """Read-only service for querying Google's predefined audience categories."""

    def _get_gaql_client(self) -> GoogleAdsServiceClient:
        sdk_client = get_sdk_client()
        return sdk_client.client.get_service("GoogleAdsService")

    def _row_to_dict(self, row: Any) -> Dict[str, Any]:
        ui = row.user_interest
        return {
            "user_interest_id": str(ui.user_interest_id),
            "name": ui.name,
            "taxonomy_type": ui.taxonomy_type.name if ui.taxonomy_type else "UNKNOWN",
            "user_interest_parent": ui.user_interest_parent or None,
            "launched_to_all": ui.launched_to_all,
            "resource_name": ui.resource_name,
        }

    async def list_user_interests(
        self,
        ctx: Context,
        customer_id: str,
        taxonomy_type: str = "AFFINITY",
        launched_to_all_only: bool = True,
        limit: int = 500,
    ) -> List[Dict[str, Any]]:
        """List predefined Google audience categories by taxonomy type.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID (used to scope the API call)
            taxonomy_type: AFFINITY, IN_MARKET, MOBILE_APP_INSTALL_USER,
                           VERTICAL_GEO, or NEW_SMART_PHONE_USER
            launched_to_all_only: When True, only return audiences available
                                  across all channels and locales
            limit: Maximum number of results to return

        Returns:
            List of user interest categories
        """
        try:
            customer_id = format_customer_id(customer_id)
            gaql = get_sdk_client().client.get_service("GoogleAdsService")

            conditions = [f"user_interest.taxonomy_type = '{taxonomy_type}'"]
            if launched_to_all_only:
                conditions.append("user_interest.launched_to_all = TRUE")

            query = (
                _BASE_QUERY
                + " WHERE "
                + " AND ".join(conditions)
                + " ORDER BY user_interest.name"
                + f" LIMIT {limit}"
            )

            response = gaql.search(customer_id=customer_id, query=query)
            results = [self._row_to_dict(row) for row in response]

            await ctx.log(
                level="info",
                message=f"Found {len(results)} user interests with taxonomy_type={taxonomy_type}",
            )
            return results

        except Exception as e:
            error_msg = f"Failed to list user interests: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def search_user_interests(
        self,
        ctx: Context,
        customer_id: str,
        keyword: str,
        taxonomy_type: Optional[str] = None,
        launched_to_all_only: bool = True,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Search predefined Google audience categories by keyword in their name.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            keyword: Search term to match against audience names (case-insensitive)
            taxonomy_type: Optional filter - AFFINITY, IN_MARKET, etc.
                           When None, searches across all taxonomy types.
            launched_to_all_only: When True, only return audiences available
                                  across all channels and locales
            limit: Maximum number of results to return

        Returns:
            List of matching user interest categories
        """
        try:
            customer_id = format_customer_id(customer_id)
            gaql = get_sdk_client().client.get_service("GoogleAdsService")

            conditions = [f"user_interest.name LIKE '%{keyword}%'"]
            if taxonomy_type:
                conditions.append(f"user_interest.taxonomy_type = '{taxonomy_type}'")
            if launched_to_all_only:
                conditions.append("user_interest.launched_to_all = TRUE")

            query = (
                _BASE_QUERY
                + " WHERE "
                + " AND ".join(conditions)
                + " ORDER BY user_interest.name"
                + f" LIMIT {limit}"
            )

            response = gaql.search(customer_id=customer_id, query=query)
            results = [self._row_to_dict(row) for row in response]

            await ctx.log(
                level="info",
                message=f"Found {len(results)} user interests matching '{keyword}'",
            )
            return results

        except Exception as e:
            error_msg = f"Failed to search user interests: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def get_user_interest(
        self,
        ctx: Context,
        customer_id: str,
        user_interest_id: str,
    ) -> Dict[str, Any]:
        """Get a specific predefined audience by its ID.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            user_interest_id: The numeric user interest ID

        Returns:
            User interest details
        """
        try:
            customer_id = format_customer_id(customer_id)
            gaql = get_sdk_client().client.get_service("GoogleAdsService")

            query = (
                _BASE_QUERY
                + f" WHERE user_interest.user_interest_id = {user_interest_id}"
            )

            response = gaql.search(customer_id=customer_id, query=query)
            for row in response:
                result = self._row_to_dict(row)
                await ctx.log(
                    level="info",
                    message=f"Retrieved user interest {user_interest_id}",
                )
                return result

            raise Exception(f"User interest {user_interest_id} not found")

        except Exception as e:
            error_msg = f"Failed to get user interest: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e


def create_user_interest_tools(
    service: UserInterestService,
) -> List[Callable[..., Awaitable[Any]]]:
    """Create MCP tool functions for the user interest service."""
    tools = []

    async def list_user_interests(
        ctx: Context,
        customer_id: str,
        taxonomy_type: str = "AFFINITY",
        launched_to_all_only: bool = True,
        limit: int = 500,
    ) -> List[Dict[str, Any]]:
        """List Google's predefined audience categories (affinity or in-market).

        These are the built-in audience segments maintained by Google, such as
        "Sports Fans", "Cooking Enthusiasts", "Auto Enthusiasts", etc.

        Args:
            customer_id: The customer ID
            taxonomy_type: Type of audience taxonomy to list:
                - AFFINITY: Audiences based on long-term interests and habits
                  (e.g. Sports Fans, Cooking Enthusiasts, Tech Enthusiasts)
                - IN_MARKET: Users actively researching or comparing products/services
                  (e.g. "Auto & Vehicles > Motor Vehicles > Cars")
                - MOBILE_APP_INSTALL_USER: Users who install apps in specific categories
                - VERTICAL_GEO: Interest-based vertical combined with geography
                - NEW_SMART_PHONE_USER: New smartphone users
            launched_to_all_only: Return only audiences available across all channels
                                  and locales (recommended: True)
            limit: Maximum number of results (default 500, max 1000)

        Returns:
            List of audience categories with:
            - user_interest_id: ID to use when targeting this audience
            - name: Human-readable category name
            - taxonomy_type: The taxonomy this audience belongs to
            - user_interest_parent: Parent category resource name (for hierarchy)
            - launched_to_all: Whether available on all channels
            - resource_name: Full resource name for API usage
        """
        return await service.list_user_interests(
            ctx=ctx,
            customer_id=customer_id,
            taxonomy_type=taxonomy_type,
            launched_to_all_only=launched_to_all_only,
            limit=limit,
        )

    async def search_user_interests(
        ctx: Context,
        customer_id: str,
        keyword: str,
        taxonomy_type: Optional[str] = None,
        launched_to_all_only: bool = True,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Search Google's predefined audiences by keyword in their name.

        Use this to find the right audience IDs before creating campaigns.
        For example, searching "football" returns affinity and in-market
        audiences related to football/soccer.

        Args:
            customer_id: The customer ID
            keyword: Search term matched against audience name (case-insensitive,
                     partial match). Examples: "football", "sport", "gaming",
                     "travel", "beauty", "automotive"
            taxonomy_type: Optional type filter:
                - AFFINITY: Long-term interests (default when targeting Display)
                - IN_MARKET: Active purchase intent
                - Omit to search across all types
            launched_to_all_only: Return only universally available audiences
            limit: Maximum number of results

        Returns:
            List of matching audience categories with their IDs and names.
            Use user_interest_id when adding this audience to a campaign or
            ad group via the ad_group_criterion or campaign_criterion tools.

        Example:
            Search "football" with taxonomy_type="AFFINITY" to find audiences
            like "Sports & Fitness > Team Sports > Soccer/Football" that can
            be used to target Display campaigns towards football fans.
        """
        return await service.search_user_interests(
            ctx=ctx,
            customer_id=customer_id,
            keyword=keyword,
            taxonomy_type=taxonomy_type,
            launched_to_all_only=launched_to_all_only,
            limit=limit,
        )

    async def get_user_interest(
        ctx: Context,
        customer_id: str,
        user_interest_id: str,
    ) -> Dict[str, Any]:
        """Get a specific predefined Google audience by its ID.

        Args:
            customer_id: The customer ID
            user_interest_id: The numeric user interest ID (from list or search)

        Returns:
            Full details of the user interest category
        """
        return await service.get_user_interest(
            ctx=ctx,
            customer_id=customer_id,
            user_interest_id=user_interest_id,
        )

    tools.extend([list_user_interests, search_user_interests, get_user_interest])
    return tools


def register_user_interest_tools(mcp: FastMCP[Any]) -> UserInterestService:
    """Register user interest tools with the MCP server."""
    service = UserInterestService()
    for tool in create_user_interest_tools(service):
        mcp.tool(tool)
    return service
