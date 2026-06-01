"""Reach plan server using SDK implementation."""

from fastmcp import FastMCP

from src.services.planning.reach_plan_service import (
    register_reach_plan_tools,
)

# Create the reach plan server
reach_plan_server = FastMCP(
    name="reach-plan-service",
    instructions="""Tools for YouTube/video reach planning and forecasting.

    Available tools:
    - list_plannable_locations: List available locations for planning
    - list_plannable_products: List available ad products for a location
      (use these to get valid plannable_product_code values)
    - generate_reach_forecast: Forecast reach, impressions, and frequency
      for a set of YouTube/video products within a budget and timeframe

    Typical workflow:
    1. list_plannable_locations → pick a location ID
    2. list_plannable_products(location_id) → pick product codes + check targeting
    3. generate_reach_forecast(location_id, planned_products, duration_days)
    """,
)

# Register the tools
register_reach_plan_tools(reach_plan_server)
