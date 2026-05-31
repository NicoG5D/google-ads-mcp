"""Local services lead server using SDK implementation."""

from fastmcp import FastMCP

from src.services.account.local_services_lead_service import (
    register_local_services_lead_tools,
)

# Create the local services lead server
local_services_lead_server = FastMCP(name="local-services-lead-service")

# Register the tools
register_local_services_lead_tools(local_services_lead_server)
