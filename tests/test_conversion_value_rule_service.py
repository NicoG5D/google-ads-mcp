"""Tests for ConversionValueRuleService."""

from typing import Any
from unittest.mock import Mock, patch

import pytest
from fastmcp import Context
from google.ads.googleads.v20.services.services.conversion_value_rule_service import (
    ConversionValueRuleServiceClient,
)
from google.ads.googleads.v20.services.services.google_ads_service import (
    GoogleAdsServiceClient,
)
from google.ads.googleads.v20.services.types.conversion_value_rule_service import (
    MutateConversionValueRulesResponse,
)

from src.services.conversions.conversion_value_rule_service import (
    ConversionValueRuleService,
    create_conversion_value_rule_tools,
    register_conversion_value_rule_tools,
)


@pytest.fixture
def mock_cvr_client() -> Mock:
    return Mock(spec=ConversionValueRuleServiceClient)


@pytest.fixture
def conversion_value_rule_service(
    mock_sdk_client: Any, mock_cvr_client: Mock
) -> ConversionValueRuleService:
    mock_sdk_client.client.get_service.return_value = mock_cvr_client
    with patch(
        "src.services.conversions.conversion_value_rule_service.get_sdk_client",
        return_value=mock_sdk_client,
    ):
        service = ConversionValueRuleService()
        _ = service.client
        return service


# ---------------------------------------------------------------------------
# create_conversion_value_rule
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_conversion_value_rule_basic(
    conversion_value_rule_service: ConversionValueRuleService,
    mock_sdk_client: Any,
    mock_cvr_client: Mock,
    mock_ctx: Context,
) -> None:
    """Test creating a basic conversion value rule."""
    mock_response = Mock(spec=MutateConversionValueRulesResponse)
    mock_cvr_client.mutate_conversion_value_rules.return_value = mock_response
    expected = {"results": [{"resource_name": "customers/123/conversionValueRules/1"}]}

    with (
        patch(
            "src.services.conversions.conversion_value_rule_service.get_sdk_client",
            return_value=mock_sdk_client,
        ),
        patch(
            "src.services.conversions.conversion_value_rule_service.serialize_proto_message",
            return_value=expected,
        ),
    ):
        result = await conversion_value_rule_service.create_conversion_value_rule(
            ctx=mock_ctx,
            customer_id="1234567890",
            action_operation="ADD",
            action_value=10.0,
        )

    assert result == expected
    mock_cvr_client.mutate_conversion_value_rules.assert_called_once()
    req = mock_cvr_client.mutate_conversion_value_rules.call_args.kwargs["request"]
    assert req.customer_id == "1234567890"
    assert len(req.operations) == 1
    rule = req.operations[0].create
    assert rule.action.value == 10.0


@pytest.mark.asyncio
async def test_create_conversion_value_rule_with_device_condition(
    conversion_value_rule_service: ConversionValueRuleService,
    mock_sdk_client: Any,
    mock_cvr_client: Mock,
    mock_ctx: Context,
) -> None:
    """Test creating a rule with a device condition."""
    mock_cvr_client.mutate_conversion_value_rules.return_value = Mock(
        spec=MutateConversionValueRulesResponse
    )

    with (
        patch(
            "src.services.conversions.conversion_value_rule_service.get_sdk_client",
            return_value=mock_sdk_client,
        ),
        patch(
            "src.services.conversions.conversion_value_rule_service.serialize_proto_message",
            return_value={},
        ),
    ):
        await conversion_value_rule_service.create_conversion_value_rule(
            ctx=mock_ctx,
            customer_id="1234567890",
            action_operation="MULTIPLY",
            action_value=1.5,
            device_types=["MOBILE"],
        )

    req = mock_cvr_client.mutate_conversion_value_rules.call_args.kwargs["request"]
    rule = req.operations[0].create
    assert len(rule.device_condition.device_types) == 1


@pytest.mark.asyncio
async def test_create_conversion_value_rule_with_geo(
    conversion_value_rule_service: ConversionValueRuleService,
    mock_sdk_client: Any,
    mock_cvr_client: Mock,
    mock_ctx: Context,
) -> None:
    """Test creating a rule with a geo condition."""
    mock_cvr_client.mutate_conversion_value_rules.return_value = Mock(
        spec=MutateConversionValueRulesResponse
    )

    with (
        patch(
            "src.services.conversions.conversion_value_rule_service.get_sdk_client",
            return_value=mock_sdk_client,
        ),
        patch(
            "src.services.conversions.conversion_value_rule_service.serialize_proto_message",
            return_value={},
        ),
    ):
        await conversion_value_rule_service.create_conversion_value_rule(
            ctx=mock_ctx,
            customer_id="1234567890",
            action_operation="ADD",
            action_value=5.0,
            geo_target_constants=["geoTargetConstants/2840"],
        )

    req = mock_cvr_client.mutate_conversion_value_rules.call_args.kwargs["request"]
    rule = req.operations[0].create
    assert "geoTargetConstants/2840" in rule.geo_location_condition.geo_target_constants


# ---------------------------------------------------------------------------
# update_conversion_value_rule
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_conversion_value_rule_status(
    conversion_value_rule_service: ConversionValueRuleService,
    mock_sdk_client: Any,
    mock_cvr_client: Mock,
    mock_ctx: Context,
) -> None:
    """Test updating a rule's status."""
    mock_cvr_client.mutate_conversion_value_rules.return_value = Mock(
        spec=MutateConversionValueRulesResponse
    )
    resource_name = "customers/1234567890/conversionValueRules/1"

    with (
        patch(
            "src.services.conversions.conversion_value_rule_service.get_sdk_client",
            return_value=mock_sdk_client,
        ),
        patch(
            "src.services.conversions.conversion_value_rule_service.serialize_proto_message",
            return_value={},
        ),
    ):
        await conversion_value_rule_service.update_conversion_value_rule(
            ctx=mock_ctx,
            customer_id="1234567890",
            rule_resource_name=resource_name,
            status="PAUSED",
        )

    req = mock_cvr_client.mutate_conversion_value_rules.call_args.kwargs["request"]
    op = req.operations[0]
    assert op.update.resource_name == resource_name
    assert "status" in list(op.update_mask.paths)


# ---------------------------------------------------------------------------
# remove_conversion_value_rule
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_remove_conversion_value_rule(
    conversion_value_rule_service: ConversionValueRuleService,
    mock_sdk_client: Any,
    mock_cvr_client: Mock,
    mock_ctx: Context,
) -> None:
    """Test removing a rule."""
    mock_cvr_client.mutate_conversion_value_rules.return_value = Mock(
        spec=MutateConversionValueRulesResponse
    )
    resource_name = "customers/1234567890/conversionValueRules/1"

    with (
        patch(
            "src.services.conversions.conversion_value_rule_service.get_sdk_client",
            return_value=mock_sdk_client,
        ),
        patch(
            "src.services.conversions.conversion_value_rule_service.serialize_proto_message",
            return_value={},
        ),
    ):
        await conversion_value_rule_service.remove_conversion_value_rule(
            ctx=mock_ctx,
            customer_id="1234567890",
            rule_resource_name=resource_name,
        )

    req = mock_cvr_client.mutate_conversion_value_rules.call_args.kwargs["request"]
    assert req.operations[0].remove == resource_name


# ---------------------------------------------------------------------------
# list_conversion_value_rules
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_conversion_value_rules(
    conversion_value_rule_service: ConversionValueRuleService,
    mock_sdk_client: Any,
    mock_cvr_client: Mock,
    mock_ctx: Context,
) -> None:
    """Test listing rules with GAQL."""
    mock_gaql = Mock(spec=GoogleAdsServiceClient)
    mock_gaql.search.return_value = [Mock(), Mock()]
    mock_sdk_client.client.get_service.return_value = mock_gaql

    with (
        patch(
            "src.services.conversions.conversion_value_rule_service.get_sdk_client",
            return_value=mock_sdk_client,
        ),
        patch(
            "src.services.conversions.conversion_value_rule_service.serialize_proto_message",
            return_value={"id": "1"},
        ),
    ):
        results = await conversion_value_rule_service.list_conversion_value_rules(
            ctx=mock_ctx,
            customer_id="1234567890",
            status_filter="ENABLED",
        )

    assert len(results) == 2


# ---------------------------------------------------------------------------
# error handling
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_error_handling(
    conversion_value_rule_service: ConversionValueRuleService,
    mock_sdk_client: Any,
    mock_cvr_client: Mock,
    mock_ctx: Context,
) -> None:
    mock_cvr_client.mutate_conversion_value_rules.side_effect = Exception("API error")

    with patch(
        "src.services.conversions.conversion_value_rule_service.get_sdk_client",
        return_value=mock_sdk_client,
    ):
        with pytest.raises(Exception, match="Failed to create conversion value rule"):
            await conversion_value_rule_service.create_conversion_value_rule(
                ctx=mock_ctx,
                customer_id="1234567890",
                action_operation="ADD",
                action_value=5.0,
            )


# ---------------------------------------------------------------------------
# tool registration
# ---------------------------------------------------------------------------


def test_register_creates_four_tools(mock_sdk_client: Any) -> None:
    from fastmcp import FastMCP

    mcp = FastMCP(name="test")
    with patch(
        "src.services.conversions.conversion_value_rule_service.get_sdk_client",
        return_value=mock_sdk_client,
    ):
        service = register_conversion_value_rule_tools(mcp)

    assert isinstance(service, ConversionValueRuleService)


def test_tool_names(mock_sdk_client: Any) -> None:
    with patch(
        "src.services.conversions.conversion_value_rule_service.get_sdk_client",
        return_value=mock_sdk_client,
    ):
        tools = create_conversion_value_rule_tools(ConversionValueRuleService())

    names = {t.__name__ for t in tools}
    assert names == {
        "create_conversion_value_rule",
        "update_conversion_value_rule",
        "remove_conversion_value_rule",
        "list_conversion_value_rules",
    }
