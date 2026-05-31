"""Recommendation subscription server using SDK implementation."""

from fastmcp import FastMCP

from src.services.planning.recommendation_subscription_service import (
    register_recommendation_subscription_tools,
)

# Create the recommendation subscription server
recommendation_subscription_server = FastMCP(
    name="recommendation-subscription-service"
)

# Register the tools
register_recommendation_subscription_tools(recommendation_subscription_server)
