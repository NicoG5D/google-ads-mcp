"""Tests for ReachPlanService."""

from typing import Any
from unittest.mock import Mock, patch

import pytest
from fastmcp import Context
from google.ads.googleads.v20.services.services.reach_plan_service import (
    ReachPlanServiceClient,
)
from google.ads.googleads.v20.services.types.reach_plan_service import (
    GenerateReachForecastResponse,
    ListPlannableLocationsResponse,
    ListPlannableProductsResponse,
)

from src.services.planning.reach_plan_service import (
    ReachPlanService,
    register_reach_plan_tools,
)


@pytest.fixture
def reach_plan_service(mock_sdk_client: Any) -> ReachPlanService:
    """Create a ReachPlanService instance with mocked dependencies."""
    # Mock ReachPlanService client
    mock_reach_plan_client = Mock(spec=ReachPlanServiceClient)
    mock_sdk_client.client.get_service.return_value = mock_reach_plan_client  # type: ignore

    with patch(
        "src.services.planning.reach_plan_service.get_sdk_client",
        return_value=mock_sdk_client,
    ):
        service = ReachPlanService()
        # Force client initialization
        _ = service.client
        return service


@pytest.mark.asyncio
async def test_list_plannable_locations(
    reach_plan_service: ReachPlanService,
    mock_sdk_client: Any,
    mock_ctx: Context,
) -> None:
    """Test listing plannable locations."""
    # Arrange
    # Create mock response
    mock_response = Mock(spec=ListPlannableLocationsResponse)
    mock_response.plannable_locations = []

    # Create mock locations
    location1 = Mock()
    location1.id = "2840"
    location1.name = "United States"
    location1.parent_country_id = None

    location2 = Mock()
    location2.id = "2826"
    location2.name = "United Kingdom"
    location2.parent_country_id = None

    location3 = Mock()
    location3.id = "21167"
    location3.name = "California"
    location3.parent_country_id = "2840"

    mock_response.plannable_locations.extend([location1, location2, location3])  # type: ignore

    # Get the mocked reach plan service client
    mock_reach_plan_client = reach_plan_service.client  # type: ignore
    mock_reach_plan_client.list_plannable_locations.return_value = mock_response  # type: ignore

    # Mock serialize_proto_message
    expected_result = {
        "plannable_locations": [
            {
                "id": "2840",
                "name": "United States",
                "parent_country_id": None,
            },
            {
                "id": "2826",
                "name": "United Kingdom",
                "parent_country_id": None,
            },
            {
                "id": "21167",
                "name": "California",
                "parent_country_id": "2840",
            },
        ]
    }

    with patch(
        "src.services.planning.reach_plan_service.serialize_proto_message",
        return_value=expected_result,
    ):
        # Act
        result = await reach_plan_service.list_plannable_locations(ctx=mock_ctx)

    # Assert
    assert result == expected_result
    assert len(result["plannable_locations"]) == 3
    assert result["plannable_locations"][0]["name"] == "United States"
    assert result["plannable_locations"][2]["parent_country_id"] == "2840"

    # Verify the API call
    mock_reach_plan_client.list_plannable_locations.assert_called_once()  # type: ignore
    call_args = mock_reach_plan_client.list_plannable_locations.call_args  # type: ignore
    request = call_args[1]["request"]
    # ListPlannableLocationsRequest has no fields to check
    assert request is not None


@pytest.mark.asyncio
async def test_list_plannable_products(
    reach_plan_service: ReachPlanService,
    mock_sdk_client: Any,
    mock_ctx: Context,
) -> None:
    """Test listing plannable products for a location."""
    # Arrange
    plannable_location_id = "2840"  # US

    # Create mock response
    mock_response = Mock(spec=ListPlannableProductsResponse)
    mock_response.product_metadata = []

    # Create mock products
    product1 = Mock()
    product1.plannable_product_code = "VIDEO_TRUEVIEW"
    product1.plannable_product_name = "YouTube Video ads"
    product1.plannable_targeting = Mock()
    product1.plannable_targeting.age_ranges = ["AGE_RANGE_18_24", "AGE_RANGE_25_34"]
    product1.plannable_targeting.genders = ["GENDER_MALE", "GENDER_FEMALE"]
    product1.plannable_targeting.devices = ["DEVICE_DESKTOP", "DEVICE_MOBILE"]
    product1.plannable_targeting.networks = ["YOUTUBE_WATCH"]

    product2 = Mock()
    product2.plannable_product_code = "DISPLAY_STANDARD"
    product2.plannable_product_name = "Display ads"
    product2.plannable_targeting = Mock()
    product2.plannable_targeting.age_ranges = ["AGE_RANGE_18_24"]
    product2.plannable_targeting.genders = ["GENDER_MALE"]
    product2.plannable_targeting.devices = ["DEVICE_MOBILE"]
    product2.plannable_targeting.networks = ["DISPLAY_NETWORK"]

    mock_response.product_metadata.extend([product1, product2])  # type: ignore

    # Get the mocked reach plan service client
    mock_reach_plan_client = reach_plan_service.client  # type: ignore
    mock_reach_plan_client.list_plannable_products.return_value = mock_response  # type: ignore

    # Act
    result = await reach_plan_service.list_plannable_products(
        ctx=mock_ctx,
        plannable_location_id=plannable_location_id,
    )

    # Assert
    assert len(result) == 2

    # Check first product
    assert result[0]["plannable_product_code"] == "VIDEO_TRUEVIEW"
    assert result[0]["plannable_product_name"] == "YouTube Video ads"
    assert len(result[0]["plannable_targeting"]["age_ranges"]) == 2
    assert "AGE_RANGE_18_24" in result[0]["plannable_targeting"]["age_ranges"]
    assert len(result[0]["plannable_targeting"]["genders"]) == 2
    assert len(result[0]["plannable_targeting"]["devices"]) == 2
    assert result[0]["plannable_targeting"]["networks"] == ["YOUTUBE_WATCH"]

    # Check second product
    assert result[1]["plannable_product_code"] == "DISPLAY_STANDARD"
    assert result[1]["plannable_product_name"] == "Display ads"

    # Verify the API call
    mock_reach_plan_client.list_plannable_products.assert_called_once()  # type: ignore
    call_args = mock_reach_plan_client.list_plannable_products.call_args  # type: ignore
    request = call_args[1]["request"]
    assert request.plannable_location_id == plannable_location_id

    # Verify logging
    mock_ctx.log.assert_called_once_with(  # type: ignore
        level="info",
        message=f"Found 2 plannable products for location {plannable_location_id}",
    )


@pytest.mark.asyncio
async def test_generate_reach_forecast_basic(
    reach_plan_service: ReachPlanService,
    mock_sdk_client: Any,
    mock_ctx: Context,
) -> None:
    """Test generate_reach_forecast with minimal required parameters."""
    mock_reach_plan_client = reach_plan_service.client  # type: ignore
    mock_response = Mock(spec=GenerateReachForecastResponse)
    mock_reach_plan_client.generate_reach_forecast.return_value = mock_response

    expected = {"reach_curve": {"reach_forecasts": []}}
    with patch(
        "src.services.planning.reach_plan_service.serialize_proto_message",
        return_value=expected,
    ):
        result = await reach_plan_service.generate_reach_forecast(
            ctx=mock_ctx,
            customer_id="1234567890",
            plannable_location_id="2840",
            planned_products=[
                {
                    "plannable_product_code": "TRUEVIEW_IN_STREAM",
                    "budget_micros": 5_000_000_000,
                }
            ],
            duration_days=30,
            currency_code="USD",
        )

    assert result == expected
    mock_reach_plan_client.generate_reach_forecast.assert_called_once()

    req = mock_reach_plan_client.generate_reach_forecast.call_args.kwargs["request"]
    assert req.customer_id == "1234567890"
    assert req.currency_code == "USD"
    assert req.campaign_duration.duration_in_days == 30
    assert req.min_effective_frequency == 1
    assert "2840" in list(req.targeting.plannable_location_ids)
    assert len(req.planned_products) == 1
    assert req.planned_products[0].plannable_product_code == "TRUEVIEW_IN_STREAM"
    assert req.planned_products[0].budget_micros == 5_000_000_000


@pytest.mark.asyncio
async def test_generate_reach_forecast_with_demographics(
    reach_plan_service: ReachPlanService,
    mock_sdk_client: Any,
    mock_ctx: Context,
) -> None:
    """Test generate_reach_forecast with age_range and gender targeting."""
    mock_reach_plan_client = reach_plan_service.client  # type: ignore
    mock_reach_plan_client.generate_reach_forecast.return_value = Mock(
        spec=GenerateReachForecastResponse
    )

    with patch(
        "src.services.planning.reach_plan_service.serialize_proto_message",
        return_value={},
    ):
        await reach_plan_service.generate_reach_forecast(
            ctx=mock_ctx,
            customer_id="1234567890",
            plannable_location_id="2840",
            planned_products=[
                {"plannable_product_code": "BUMPER", "budget_micros": 1_000_000_000}
            ],
            duration_days=14,
            age_range="AGE_RANGE_18_34",
            genders=["MALE", "FEMALE"],
        )

    req = mock_reach_plan_client.generate_reach_forecast.call_args.kwargs["request"]
    assert req.campaign_duration.duration_in_days == 14
    # age_range set
    from google.ads.googleads.v20.enums.types.reach_plan_age_range import (
        ReachPlanAgeRangeEnum,
    )

    assert (
        req.targeting.age_range
        == ReachPlanAgeRangeEnum.ReachPlanAgeRange.AGE_RANGE_18_34
    )
    # genders set
    assert len(req.targeting.genders) == 2


@pytest.mark.asyncio
async def test_generate_reach_forecast_multiple_products(
    reach_plan_service: ReachPlanService,
    mock_sdk_client: Any,
    mock_ctx: Context,
) -> None:
    """Test generate_reach_forecast with multiple planned products."""
    mock_reach_plan_client = reach_plan_service.client  # type: ignore
    mock_reach_plan_client.generate_reach_forecast.return_value = Mock(
        spec=GenerateReachForecastResponse
    )

    with patch(
        "src.services.planning.reach_plan_service.serialize_proto_message",
        return_value={},
    ):
        await reach_plan_service.generate_reach_forecast(
            ctx=mock_ctx,
            customer_id="1234567890",
            plannable_location_id="2840",
            planned_products=[
                {
                    "plannable_product_code": "TRUEVIEW_IN_STREAM",
                    "budget_micros": 3_000_000_000,
                },
                {"plannable_product_code": "BUMPER", "budget_micros": 2_000_000_000},
            ],
        )

    req = mock_reach_plan_client.generate_reach_forecast.call_args.kwargs["request"]
    assert len(req.planned_products) == 2
    codes = {p.plannable_product_code for p in req.planned_products}
    assert codes == {"TRUEVIEW_IN_STREAM", "BUMPER"}


@pytest.mark.asyncio
async def test_generate_reach_forecast_google_ads_error(
    reach_plan_service: ReachPlanService,
    mock_sdk_client: Any,
    mock_ctx: Context,
    google_ads_exception: Any,
) -> None:
    """Test error handling when Google Ads API returns an error."""
    mock_reach_plan_client = reach_plan_service.client  # type: ignore
    mock_reach_plan_client.generate_reach_forecast.side_effect = google_ads_exception

    with pytest.raises(Exception, match="Failed to generate reach forecast"):
        await reach_plan_service.generate_reach_forecast(
            ctx=mock_ctx,
            customer_id="1234567890",
            plannable_location_id="2840",
            planned_products=[
                {
                    "plannable_product_code": "TRUEVIEW_IN_STREAM",
                    "budget_micros": 1_000_000_000,
                }
            ],
        )


@pytest.mark.asyncio
async def test_error_handling_list_locations(
    reach_plan_service: ReachPlanService,
    mock_sdk_client: Any,
    mock_ctx: Context,
    google_ads_exception: Any,
) -> None:
    """Test error handling when listing locations fails."""
    # Arrange
    # Get the mocked reach plan service client and make it raise exception
    mock_reach_plan_client = reach_plan_service.client  # type: ignore
    mock_reach_plan_client.list_plannable_locations.side_effect = google_ads_exception  # type: ignore

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        await reach_plan_service.list_plannable_locations(ctx=mock_ctx)

    assert "Failed to list plannable locations" in str(exc_info.value)
    assert "Test Google Ads Exception" in str(exc_info.value)

    # Verify error logging
    mock_ctx.log.assert_called_once_with(  # type: ignore
        level="error",
        message="Failed to list plannable locations: Test Google Ads Exception",
    )


@pytest.mark.asyncio
async def test_error_handling_list_products(
    reach_plan_service: ReachPlanService,
    mock_sdk_client: Any,
    mock_ctx: Context,
    google_ads_exception: Any,
) -> None:
    """Test error handling when listing products fails."""
    # Arrange
    plannable_location_id = "2840"

    # Get the mocked reach plan service client and make it raise exception
    mock_reach_plan_client = reach_plan_service.client  # type: ignore
    mock_reach_plan_client.list_plannable_products.side_effect = google_ads_exception  # type: ignore

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        await reach_plan_service.list_plannable_products(
            ctx=mock_ctx,
            plannable_location_id=plannable_location_id,
        )

    assert "Failed to list plannable products" in str(exc_info.value)
    assert "Test Google Ads Exception" in str(exc_info.value)

    # Verify error logging
    mock_ctx.log.assert_called_once_with(  # type: ignore
        level="error",
        message="Failed to list plannable products: Test Google Ads Exception",
    )


def test_register_reach_plan_tools() -> None:
    """Test tool registration."""
    # Arrange
    mock_mcp = Mock()

    # Act
    service = register_reach_plan_tools(mock_mcp)

    # Assert
    assert isinstance(service, ReachPlanService)

    # Verify that tools were registered
    assert mock_mcp.tool.call_count == 3  # 3 tools registered  # type: ignore

    # Verify tool functions were passed
    registered_tools = [call[0][0] for call in mock_mcp.tool.call_args_list]  # type: ignore
    tool_names = [tool.__name__ for tool in registered_tools]

    expected_tools = [
        "list_plannable_locations",
        "list_plannable_products",
        "generate_reach_forecast",
    ]

    assert set(tool_names) == set(expected_tools)
