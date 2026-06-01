"""Customer SkAdNetwork Conversion Value Schema service implementation with full v20 type safety."""

from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastmcp import Context, FastMCP
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.v20.resources.types.customer_sk_ad_network_conversion_value_schema import (
    CustomerSkAdNetworkConversionValueSchema,
)
from google.ads.googleads.v20.services.services.customer_sk_ad_network_conversion_value_schema_service import (
    CustomerSkAdNetworkConversionValueSchemaServiceClient,
)
from google.ads.googleads.v20.services.types.customer_sk_ad_network_conversion_value_schema_service import (
    CustomerSkAdNetworkConversionValueSchemaOperation,
    MutateCustomerSkAdNetworkConversionValueSchemaRequest,
    MutateCustomerSkAdNetworkConversionValueSchemaResponse,
)

from src.sdk_client import get_sdk_client
from src.utils import (
    format_ads_error,
    resolve_customer_id,
    get_logger,
    serialize_proto_message,
)

logger = get_logger(__name__)


class CustomerSkAdNetworkConversionValueSchemaService:
    """Service for managing Customer SkAdNetwork Conversion Value Schemas.

    Manages the Apple SKAdNetwork conversion value schema that maps
    fine-grained or coarse conversion values to advertiser-defined
    conversion events for iOS app campaigns.
    """

    def __init__(self) -> None:
        self._client: Optional[
            CustomerSkAdNetworkConversionValueSchemaServiceClient
        ] = None

    @property
    def client(self) -> CustomerSkAdNetworkConversionValueSchemaServiceClient:
        if self._client is None:
            sdk_client = get_sdk_client()
            self._client = sdk_client.client.get_service(
                "CustomerSkAdNetworkConversionValueSchemaService", version="v20"
            )
        assert self._client is not None
        return self._client

    async def mutate_skan_conversion_value_schema(
        self,
        ctx: Context,
        *,
        customer_id: Optional[str] = None,
        resource_name: str,
        validate_only: bool = False,
        enable_warnings: bool = False,
    ) -> Dict[str, Any]:
        """Update the Customer SkAdNetwork Conversion Value Schema.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID whose schema to update
            resource_name: Resource name of the schema to update
                (format: "customers/{customer_id}/customerSkAdNetworkConversionValueSchemas/{id}")
            validate_only: If True, validates but does not execute the operation
            enable_warnings: If True, returns warnings alongside results

        Returns:
            Mutate result with resource name and app ID, plus optional warnings
        """
        try:
            formatted_customer_id = resolve_customer_id(customer_id)

            schema = CustomerSkAdNetworkConversionValueSchema()
            schema.resource_name = resource_name

            operation = CustomerSkAdNetworkConversionValueSchemaOperation()
            operation.update = schema

            request = MutateCustomerSkAdNetworkConversionValueSchemaRequest()
            request.customer_id = formatted_customer_id
            request.operation = operation
            request.validate_only = validate_only
            request.enable_warnings = enable_warnings

            response: MutateCustomerSkAdNetworkConversionValueSchemaResponse = (
                self.client.mutate_skan_conversion_value_schema(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Mutated SkAdNetwork conversion value schema for customer "
                f"{formatted_customer_id}: {resource_name}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = (
                f"Failed to mutate SkAdNetwork conversion value schema: {str(e)}"
            )
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e


def create_customer_sk_ad_network_conversion_value_schema_tools(
    service: CustomerSkAdNetworkConversionValueSchemaService,
) -> List[Callable[..., Awaitable[Any]]]:
    """Create tool functions for the customer SkAdNetwork conversion value schema service."""
    tools = []

    async def mutate_skan_conversion_value_schema(
        ctx: Context,
        *,
        customer_id: Optional[str] = None,
        resource_name: str,
        validate_only: bool = False,
        enable_warnings: bool = False,
    ) -> Dict[str, Any]:
        """Update the Apple SKAdNetwork conversion value schema for a customer.

        Updates the mapping between Apple's SKAdNetwork fine-grained or
        coarse conversion values and Google Ads conversion events. This schema
        is used to optimize iOS app campaigns via Apple's privacy-preserving
        attribution framework.

        Args:
            customer_id: The customer ID (with or without hyphens)
            resource_name: Resource name of the schema to update
                (format: "customers/{customer_id}/customerSkAdNetworkConversionValueSchemas/{id}")
            validate_only: If True, the request is validated but not applied.
                Only errors are returned (default: False)
            enable_warnings: If True, schema validation warnings are returned
                alongside results (default: False)

        Returns:
            Mutate result including the resource name and Apple App Store app ID,
            and optionally any schema validation warnings

        Example:
            result = await mutate_skan_conversion_value_schema(
                customer_id="1234567890",
                resource_name="customers/1234567890/customerSkAdNetworkConversionValueSchemas/987654321"
            )
        """
        return await service.mutate_skan_conversion_value_schema(
            ctx=ctx,
            customer_id=customer_id,
            resource_name=resource_name,
            validate_only=validate_only,
            enable_warnings=enable_warnings,
        )

    tools.append(mutate_skan_conversion_value_schema)
    return tools


def register_customer_sk_ad_network_conversion_value_schema_tools(
    mcp: FastMCP[Any],
) -> CustomerSkAdNetworkConversionValueSchemaService:
    """Register customer SkAdNetwork conversion value schema tools with the MCP server.

    Returns the service instance for testing purposes.
    """
    service = CustomerSkAdNetworkConversionValueSchemaService()
    tools = create_customer_sk_ad_network_conversion_value_schema_tools(service)

    for tool in tools:
        mcp.tool(tool)

    return service
