"""Third-party app analytics link server using SDK implementation."""

from fastmcp import FastMCP

from src.services.product_integration.third_party_app_analytics_link_service import (
    register_third_party_app_analytics_link_tools,
)

# Create the third-party app analytics link server
third_party_app_analytics_link_server = FastMCP(
    name="third-party-app-analytics-link-service"
)

# Register the tools
register_third_party_app_analytics_link_tools(third_party_app_analytics_link_server)
