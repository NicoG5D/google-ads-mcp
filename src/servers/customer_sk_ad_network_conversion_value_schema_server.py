"""Customer SkAdNetwork conversion value schema server using SDK implementation."""

from fastmcp import FastMCP

from src.services.account.customer_sk_ad_network_conversion_value_schema_service import (
    register_customer_sk_ad_network_conversion_value_schema_tools,
)

# Create the customer SkAdNetwork conversion value schema server
customer_sk_ad_network_conversion_value_schema_server = FastMCP(
    name="customer-sk-ad-network-conversion-value-schema-service"
)

# Register the tools
register_customer_sk_ad_network_conversion_value_schema_tools(
    customer_sk_ad_network_conversion_value_schema_server
)
