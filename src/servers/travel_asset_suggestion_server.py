"""Travel asset suggestion server using SDK implementation."""

from fastmcp import FastMCP

from src.services.assets.travel_asset_suggestion_service import (
    register_travel_asset_suggestion_tools,
)

# Create the travel asset suggestion server
travel_asset_suggestion_server = FastMCP(name="travel-asset-suggestion-service")

# Register the tools
register_travel_asset_suggestion_tools(travel_asset_suggestion_server)
