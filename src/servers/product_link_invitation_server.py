"""Product link invitation server using SDK implementation."""

from fastmcp import FastMCP

from src.services.product_integration.product_link_invitation_service import (
    register_product_link_invitation_tools,
)

# Create the product link invitation server
product_link_invitation_server = FastMCP(name="product-link-invitation-service")

# Register the tools
register_product_link_invitation_tools(product_link_invitation_server)
