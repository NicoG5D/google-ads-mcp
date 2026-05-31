"""Local Services Lead service implementation with full v20 type safety."""

from typing import Any, Awaitable, Callable, Dict, List, Optional, Sequence

from fastmcp import Context, FastMCP
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.v20.services.services.local_services_lead_service import (
    LocalServicesLeadServiceClient,
)
from google.ads.googleads.v20.services.types.local_services_lead_service import (
    AppendLeadConversationRequest,
    AppendLeadConversationResponse,
    Conversation,
)

from src.sdk_client import get_sdk_client
from src.utils import (
    format_ads_error,
    format_customer_id,
    get_logger,
    serialize_proto_message,
)

logger = get_logger(__name__)


class LocalServicesLeadService:
    """Service for managing Local Services Ads leads in Google Ads.

    Provides operations to append conversation messages to local services
    leads, enabling providers to track communication with prospective
    customers.
    """

    def __init__(self) -> None:
        self._client: Optional[LocalServicesLeadServiceClient] = None

    @property
    def client(self) -> LocalServicesLeadServiceClient:
        if self._client is None:
            sdk_client = get_sdk_client()
            self._client = sdk_client.client.get_service(
                "LocalServicesLeadService", version="v20"
            )
        assert self._client is not None
        return self._client

    async def append_lead_conversation(
        self,
        ctx: Context,
        customer_id: str,
        conversations: Sequence[Dict[str, str]],
    ) -> Dict[str, Any]:
        """Append conversation messages to local services leads.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID owning the leads
            conversations: List of conversation dicts, each containing:
                - local_services_lead: Resource name of the lead
                  (e.g. "customers/123/localServicesLeads/456")
                - text: The message text to append

        Returns:
            List of conversation results or partial failure errors
        """
        try:
            formatted_customer_id = format_customer_id(customer_id)

            conv_messages: List[Conversation] = []
            for conv_data in conversations:
                conv = Conversation()
                conv.local_services_lead = conv_data["local_services_lead"]
                conv.text = conv_data["text"]
                conv_messages.append(conv)

            request = AppendLeadConversationRequest()
            request.customer_id = formatted_customer_id
            request.conversations = conv_messages

            response: AppendLeadConversationResponse = (
                self.client.append_lead_conversation(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Appended {len(conversations)} conversation(s) to leads "
                f"for customer {formatted_customer_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to append lead conversation: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e


def create_local_services_lead_tools(
    service: LocalServicesLeadService,
) -> List[Callable[..., Awaitable[Any]]]:
    """Create tool functions for the local services lead service."""
    tools = []

    async def append_lead_conversation(
        ctx: Context,
        customer_id: str,
        conversations: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """Append conversation messages to Local Services Ads leads.

        Adds text conversation entries to existing Local Services leads,
        allowing providers to record communication history with customers
        who have submitted lead requests.

        Args:
            customer_id: The customer ID (with or without hyphens)
            conversations: List of conversation entries, each with:
                - local_services_lead: The lead resource name
                  (format: "customers/{customer_id}/localServicesLeads/{lead_id}")
                - text: The message text to append to the lead

        Returns:
            Response with results for each conversation append operation,
            including the new conversation resource name on success or
            a partial failure error on failure

        Example:
            result = await append_lead_conversation(
                customer_id="1234567890",
                conversations=[
                    {
                        "local_services_lead": "customers/1234567890/localServicesLeads/987654",
                        "text": "Called customer back, left voicemail."
                    }
                ]
            )
        """
        return await service.append_lead_conversation(
            ctx=ctx,
            customer_id=customer_id,
            conversations=conversations,
        )

    tools.append(append_lead_conversation)
    return tools


def register_local_services_lead_tools(
    mcp: FastMCP[Any],
) -> LocalServicesLeadService:
    """Register local services lead tools with the MCP server.

    Returns the service instance for testing purposes.
    """
    service = LocalServicesLeadService()
    tools = create_local_services_lead_tools(service)

    for tool in tools:
        mcp.tool(tool)

    return service
