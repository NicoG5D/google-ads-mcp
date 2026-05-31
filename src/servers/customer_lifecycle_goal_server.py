"""Customer lifecycle goal server using SDK implementation."""

from fastmcp import FastMCP

from src.services.account.customer_lifecycle_goal_service import (
    register_customer_lifecycle_goal_tools,
)

# Create the customer lifecycle goal server
customer_lifecycle_goal_server = FastMCP(name="customer-lifecycle-goal-service")

# Register the tools
register_customer_lifecycle_goal_tools(customer_lifecycle_goal_server)
