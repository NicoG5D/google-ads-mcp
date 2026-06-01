"""User List Customer Type service implementation with full v20 type safety."""

from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastmcp import Context, FastMCP
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.v20.enums.types.user_list_customer_type_category import (
    UserListCustomerTypeCategoryEnum,
)
from google.ads.googleads.v20.resources.types.user_list_customer_type import (
    UserListCustomerType,
)
from google.ads.googleads.v20.services.services.user_list_customer_type_service import (
    UserListCustomerTypeServiceClient,
)
from google.ads.googleads.v20.services.types.user_list_customer_type_service import (
    MutateUserListCustomerTypesRequest,
    MutateUserListCustomerTypesResponse,
    UserListCustomerTypeOperation,
)

from src.sdk_client import get_sdk_client
from src.utils import (
    format_ads_error,
    resolve_customer_id,
    get_logger,
    resolve_enum,
    serialize_proto_message,
)

logger = get_logger(__name__)


class UserListCustomerTypeService:
    """Service for managing user list customer types in Google Ads.

    UserListCustomerType attaches a customer type category to a user list,
    enabling segmentation of user lists by customer lifecycle stage.
    """

    def __init__(self) -> None:
        self._client: Optional[UserListCustomerTypeServiceClient] = None

    @property
    def client(self) -> UserListCustomerTypeServiceClient:
        if self._client is None:
            sdk_client = get_sdk_client()
            self._client = sdk_client.client.get_service(
                "UserListCustomerTypeService", version="v20"
            )
        assert self._client is not None
        return self._client

    async def attach_user_list_customer_type(
        self,
        ctx: Context,
        *,
        customer_id: Optional[str] = None,
        user_list: str,
        customer_type_category: UserListCustomerTypeCategoryEnum.UserListCustomerTypeCategory,
        partial_failure: bool = False,
        validate_only: bool = False,
    ) -> Dict[str, Any]:
        """Attach a customer type category to a user list.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            user_list: The resource name of the user list
            customer_type_category: The customer type category to attach
            partial_failure: If true, valid operations succeed even if others fail
            validate_only: If true, only validates without executing

        Returns:
            Created user list customer type details
        """
        try:
            customer_id = resolve_customer_id(customer_id)

            user_list_customer_type = UserListCustomerType()
            user_list_customer_type.user_list = user_list
            user_list_customer_type.customer_type_category = customer_type_category

            operation = UserListCustomerTypeOperation()
            operation.create = user_list_customer_type

            request = MutateUserListCustomerTypesRequest()
            request.customer_id = customer_id
            request.operations = [operation]
            request.partial_failure = partial_failure
            request.validate_only = validate_only

            response: MutateUserListCustomerTypesResponse = (
                self.client.mutate_user_list_customer_types(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Attached customer type {customer_type_category} to user list {user_list} for customer {customer_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to attach user list customer type: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def detach_user_list_customer_type(
        self,
        ctx: Context,
        *,
        customer_id: Optional[str] = None,
        user_list_id: str,
        customer_type_category: str,
        partial_failure: bool = False,
        validate_only: bool = False,
    ) -> Dict[str, Any]:
        """Detach a customer type category from a user list.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            user_list_id: The user list ID
            customer_type_category: The customer type category string identifier
            partial_failure: If true, valid operations succeed even if others fail
            validate_only: If true, only validates without executing

        Returns:
            Removal result details
        """
        try:
            customer_id = resolve_customer_id(customer_id)
            resource_name = f"customers/{customer_id}/userListCustomerTypes/{user_list_id}~{customer_type_category}"

            operation = UserListCustomerTypeOperation()
            operation.remove = resource_name

            request = MutateUserListCustomerTypesRequest()
            request.customer_id = customer_id
            request.operations = [operation]
            request.partial_failure = partial_failure
            request.validate_only = validate_only

            response: MutateUserListCustomerTypesResponse = (
                self.client.mutate_user_list_customer_types(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Detached customer type {customer_type_category} from user list {user_list_id} for customer {customer_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to detach user list customer type: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e


def create_user_list_customer_type_tools(
    service: UserListCustomerTypeService,
) -> List[Callable[..., Awaitable[Any]]]:
    """Create tool functions for the user list customer type service."""
    tools = []

    async def attach_user_list_customer_type(
        ctx: Context,
        *,
        customer_id: Optional[str] = None,
        user_list: str,
        customer_type_category: str,
        partial_failure: bool = False,
        validate_only: bool = False,
    ) -> Dict[str, Any]:
        """Attach a customer type category to a user list.

        Customer type categories segment user lists by customer lifecycle stage,
        allowing campaigns to optimize for acquisition of new customers vs.
        re-engaging existing ones.

        Args:
            customer_id: The customer ID
            user_list: Resource name of the user list
                (e.g. customers/123/userLists/456)
            customer_type_category: The customer type category to attach
                (e.g. PURCHASERS, ALL_CUSTOMERS, HIGH_VALUE_CUSTOMERS)
            partial_failure: If true, valid operations succeed even if others fail
            validate_only: If true, only validates without executing

        Returns:
            Created user list customer type details

        Example:
            result = await attach_user_list_customer_type(
                customer_id="1234567890",
                user_list="customers/1234567890/userLists/111",
                customer_type_category="PURCHASERS"
            )
        """
        category_enum = resolve_enum(
            UserListCustomerTypeCategoryEnum.UserListCustomerTypeCategory,
            customer_type_category,
            "customer_type_category",
        )
        return await service.attach_user_list_customer_type(
            ctx=ctx,
            customer_id=customer_id,
            user_list=user_list,
            customer_type_category=category_enum,
            partial_failure=partial_failure,
            validate_only=validate_only,
        )

    async def detach_user_list_customer_type(
        ctx: Context,
        *,
        customer_id: Optional[str] = None,
        user_list_id: str,
        customer_type_category: str,
        partial_failure: bool = False,
        validate_only: bool = False,
    ) -> Dict[str, Any]:
        """Detach a customer type category from a user list.

        Args:
            customer_id: The customer ID
            user_list_id: The user list ID
            customer_type_category: The customer type category to detach
                (e.g. PURCHASERS, ALL_CUSTOMERS, HIGH_VALUE_CUSTOMERS)
            partial_failure: If true, valid operations succeed even if others fail
            validate_only: If true, only validates without executing

        Returns:
            Removal result details

        Example:
            result = await detach_user_list_customer_type(
                customer_id="1234567890",
                user_list_id="111",
                customer_type_category="PURCHASERS"
            )
        """
        return await service.detach_user_list_customer_type(
            ctx=ctx,
            customer_id=customer_id,
            user_list_id=user_list_id,
            customer_type_category=customer_type_category,
            partial_failure=partial_failure,
            validate_only=validate_only,
        )

    tools.extend([attach_user_list_customer_type, detach_user_list_customer_type])
    return tools


def register_user_list_customer_type_tools(
    mcp: FastMCP[Any],
) -> UserListCustomerTypeService:
    """Register user list customer type tools with the MCP server.

    Returns the service instance for testing purposes.
    """
    service = UserListCustomerTypeService()
    tools = create_user_list_customer_type_tools(service)

    for tool in tools:
        mcp.tool(tool)

    return service
