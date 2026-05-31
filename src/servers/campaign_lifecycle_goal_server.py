"""Campaign lifecycle goal server using SDK implementation."""

from fastmcp import FastMCP

from src.services.campaign.campaign_lifecycle_goal_service import (
    register_campaign_lifecycle_goal_tools,
)

# Create the campaign lifecycle goal server
campaign_lifecycle_goal_server = FastMCP(name="campaign-lifecycle-goal-service")

# Register the tools
register_campaign_lifecycle_goal_tools(campaign_lifecycle_goal_server)
