"""Content creator insights server using SDK implementation."""

from fastmcp import FastMCP

from src.services.planning.content_creator_insights_service import (
    register_content_creator_insights_tools,
)

# Create the content creator insights server
content_creator_insights_server = FastMCP(name="content-creator-insights-service")

# Register the tools
register_content_creator_insights_tools(content_creator_insights_server)
