"""Batch job service implementation using Google Ads SDK."""

from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastmcp import Context, FastMCP
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.v20.resources.types.batch_job import BatchJob
from google.ads.googleads.v20.services.services.batch_job_service import (
    BatchJobServiceClient,
)
from google.ads.googleads.v20.services.types.batch_job_service import (
    AddBatchJobOperationsRequest,
    AddBatchJobOperationsResponse,
    BatchJobOperation,
    ListBatchJobResultsRequest,
    MutateBatchJobRequest,
    MutateBatchJobResponse,
    RunBatchJobRequest,
)
from google.ads.googleads.v20.services.services.google_ads_service import (
    GoogleAdsServiceClient,
)
from google.ads.googleads.v20.services.types.google_ads_service import MutateOperation

from src.sdk_client import get_sdk_client
from src.utils import (
    format_ads_error,
    format_customer_id,
    get_logger,
    serialize_proto_message,
)

logger = get_logger(__name__)


class BatchJobService:
    """Batch job service for performing bulk operations."""

    def __init__(self) -> None:
        """Initialize the batch job service."""
        self._client: Optional[BatchJobServiceClient] = None

    @property
    def client(self) -> BatchJobServiceClient:
        """Get the batch job service client."""
        if self._client is None:
            sdk_client = get_sdk_client()
            self._client = sdk_client.client.get_service(
                "BatchJobService", version="v20"
            )
        assert self._client is not None
        return self._client

    async def create_batch_job(
        self,
        ctx: Context,
        customer_id: str,
    ) -> Dict[str, Any]:
        """Create a new batch job.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID

        Returns:
            Created batch job details
        """
        try:
            customer_id = format_customer_id(customer_id)

            # Create batch job
            batch_job = BatchJob()

            # Create operation
            operation = BatchJobOperation()
            operation.create = batch_job

            # Create request
            request = MutateBatchJobRequest()
            request.customer_id = customer_id
            request.operation = operation

            # Make the API call
            response: MutateBatchJobResponse = self.client.mutate_batch_job(
                request=request
            )

            await ctx.log(
                level="info",
                message=f"Created batch job for customer {customer_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to create batch job: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def get_batch_job(
        self,
        ctx: Context,
        customer_id: str,
        batch_job_resource_name: str,
    ) -> Dict[str, Any]:
        """Get batch job details.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            batch_job_resource_name: The batch job resource name

        Returns:
            Batch job details
        """
        try:
            customer_id = format_customer_id(customer_id)

            # Use GoogleAdsService for search instead of get_batch_job
            sdk_client = get_sdk_client()
            google_ads_service: GoogleAdsServiceClient = sdk_client.client.get_service(
                "GoogleAdsService"
            )

            # Extract batch job ID from resource name
            batch_job_id = batch_job_resource_name.split("/")[-1]

            query = f"""
                SELECT
                    batch_job.resource_name,
                    batch_job.id,
                    batch_job.status,
                    batch_job.long_running_operation,
                    batch_job.metadata.creation_date_time,
                    batch_job.metadata.start_date_time,
                    batch_job.metadata.completion_date_time,
                    batch_job.metadata.estimated_completion_ratio,
                    batch_job.metadata.operation_count,
                    batch_job.metadata.executed_operation_count
                FROM batch_job
                WHERE batch_job.id = {batch_job_id}
            """

            response = google_ads_service.search(customer_id=customer_id, query=query)

            for row in response:
                await ctx.log(
                    level="info",
                    message="Retrieved batch job details",
                )
                return serialize_proto_message(row)

            raise Exception(f"Batch job with ID {batch_job_id} not found")

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to get batch job: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    def _build_mutate_operation(self, op: Any, customer_id: str) -> MutateOperation:
        """Build a MutateOperation from a simplified operation dict.

        Supported types:
          campaign_budget: create(name, amount_micros) | update(resource_name, amount_micros) | remove(resource_name)
          campaign: update(resource_name, name?, status?) | remove(resource_name)
          ad_group: create(name, campaign_id, cpc_bid_micros?) | update(resource_name, ...) | remove(resource_name)
          ad_group_criterion/keyword: create(ad_group_id, text, match_type?) | remove(resource_name)
        """
        from google.ads.googleads.v20.enums.types.campaign_status import (
            CampaignStatusEnum,
        )
        from google.ads.googleads.v20.enums.types.ad_group_status import (
            AdGroupStatusEnum,
        )
        from google.ads.googleads.v20.enums.types.keyword_match_type import (
            KeywordMatchTypeEnum,
        )
        from google.ads.googleads.v20.resources.types.campaign_budget import (
            CampaignBudget,
        )
        from google.ads.googleads.v20.resources.types.campaign import Campaign
        from google.ads.googleads.v20.resources.types.ad_group import AdGroup
        from google.ads.googleads.v20.resources.types.ad_group_criterion import (
            AdGroupCriterion,
        )
        from google.ads.googleads.v20.common.types.criteria import KeywordInfo
        from google.ads.googleads.v20.services.types.campaign_budget_service import (
            CampaignBudgetOperation,
        )
        from google.ads.googleads.v20.services.types.campaign_service import (
            CampaignOperation,
        )
        from google.ads.googleads.v20.services.types.ad_group_service import (
            AdGroupOperation,
        )
        from google.ads.googleads.v20.services.types.ad_group_criterion_service import (
            AdGroupCriterionOperation,
        )
        from google.protobuf import field_mask_pb2

        op_type = op.get("type", "")
        action = op.get("action", "create")
        mutate_op = MutateOperation()

        if op_type == "campaign_budget":
            budget_op = CampaignBudgetOperation()
            if action == "create":
                budget = CampaignBudget()
                budget.name = op["name"]
                budget.amount_micros = op["amount_micros"]
                budget.explicitly_shared = op.get("explicitly_shared", True)
                budget_op.create = budget
            elif action == "update":
                budget = CampaignBudget()
                budget.resource_name = op["resource_name"]
                fields = []
                if "amount_micros" in op:
                    budget.amount_micros = op["amount_micros"]
                    fields.append("amount_micros")
                budget_op.update = budget
                budget_op.update_mask.CopyFrom(field_mask_pb2.FieldMask(paths=fields))
            elif action == "remove":
                budget_op.remove = op["resource_name"]
            mutate_op.campaign_budget_operation = budget_op

        elif op_type == "campaign":
            campaign_op = CampaignOperation()
            if action == "update":
                campaign = Campaign()
                campaign.resource_name = op["resource_name"]
                fields = []
                if "name" in op:
                    campaign.name = op["name"]
                    fields.append("name")
                if "status" in op:
                    campaign.status = getattr(
                        CampaignStatusEnum.CampaignStatus, op["status"]
                    )
                    fields.append("status")
                campaign_op.update = campaign
                campaign_op.update_mask.CopyFrom(field_mask_pb2.FieldMask(paths=fields))
            elif action == "remove":
                campaign_op.remove = op["resource_name"]
            mutate_op.campaign_operation = campaign_op

        elif op_type == "ad_group":
            ag_op = AdGroupOperation()
            if action == "create":
                ad_group = AdGroup()
                ad_group.name = op["name"]
                ad_group.campaign = (
                    f"customers/{customer_id}/campaigns/{op['campaign_id']}"
                )
                if "cpc_bid_micros" in op:
                    ad_group.cpc_bid_micros = op["cpc_bid_micros"]
                ag_op.create = ad_group
            elif action == "update":
                ad_group = AdGroup()
                ad_group.resource_name = op["resource_name"]
                fields = []
                if "name" in op:
                    ad_group.name = op["name"]
                    fields.append("name")
                if "status" in op:
                    ad_group.status = getattr(
                        AdGroupStatusEnum.AdGroupStatus, op["status"]
                    )
                    fields.append("status")
                if "cpc_bid_micros" in op:
                    ad_group.cpc_bid_micros = op["cpc_bid_micros"]
                    fields.append("cpc_bid_micros")
                ag_op.update = ad_group
                ag_op.update_mask.CopyFrom(field_mask_pb2.FieldMask(paths=fields))
            elif action == "remove":
                ag_op.remove = op["resource_name"]
            mutate_op.ad_group_operation = ag_op

        elif op_type in ("ad_group_criterion", "keyword"):
            crit_op = AdGroupCriterionOperation()
            if action == "create":
                criterion = AdGroupCriterion()
                criterion.ad_group = (
                    f"customers/{customer_id}/adGroups/{op['ad_group_id']}"
                )
                keyword = KeywordInfo()
                keyword.text = op["text"]
                keyword.match_type = getattr(
                    KeywordMatchTypeEnum.KeywordMatchType,
                    op.get("match_type", "BROAD"),
                )
                criterion.keyword = keyword
                crit_op.create = criterion
            elif action == "remove":
                crit_op.remove = op["resource_name"]
            mutate_op.ad_group_criterion_operation = crit_op

        else:
            raise ValueError(
                f"Unsupported operation type '{op_type}'. "
                "Supported: campaign_budget, campaign, ad_group, ad_group_criterion/keyword"
            )

        return mutate_op

    async def add_operations_to_batch_job(
        self,
        ctx: Context,
        customer_id: str,
        batch_job_resource_name: str,
        operations_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Add operations to a batch job.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            batch_job_resource_name: The batch job resource name
            operations_data: List of operation data (simplified format)

        Returns:
            Result of adding operations
        """
        try:
            customer_id = format_customer_id(customer_id)

            operations = [
                self._build_mutate_operation(op, customer_id) for op in operations_data
            ]

            request = AddBatchJobOperationsRequest()
            request.resource_name = batch_job_resource_name
            request.sequence_token = ""
            request.mutate_operations = operations

            response: AddBatchJobOperationsResponse = (
                self.client.add_batch_job_operations(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Added {len(operations)} operations to batch job",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to add operations to batch job: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def run_batch_job(
        self,
        ctx: Context,
        customer_id: str,
        batch_job_resource_name: str,
    ) -> Dict[str, Any]:
        """Run a batch job.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            batch_job_resource_name: The batch job resource name

        Returns:
            Batch job execution details
        """
        try:
            customer_id = format_customer_id(customer_id)

            # Create request
            request = RunBatchJobRequest()
            request.resource_name = batch_job_resource_name

            # Make the API call
            operation = self.client.run_batch_job(request=request)

            await ctx.log(
                level="info",
                message="Started batch job execution",
            )

            return {
                "batch_job_resource_name": batch_job_resource_name,
                "long_running_operation": str(operation),  # type: ignore
                "status": "RUNNING",
            }

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to run batch job: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def list_batch_job_results(
        self,
        ctx: Context,
        customer_id: str,
        batch_job_resource_name: str,
        page_size: int = 1000,
        page_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List batch job results.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            batch_job_resource_name: The batch job resource name
            page_size: Number of results per page
            page_token: Token for pagination

        Returns:
            Batch job results
        """
        try:
            customer_id = format_customer_id(customer_id)

            # Create request
            request = ListBatchJobResultsRequest()
            request.resource_name = batch_job_resource_name
            request.page_size = page_size
            if page_token:
                request.page_token = page_token

            # Make the API call
            response = self.client.list_batch_job_results(request=request)

            await ctx.log(
                level="info",
                message="Retrieved batch job results",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = format_ads_error(e)
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to list batch job results: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def list_batch_jobs(
        self,
        ctx: Context,
        customer_id: str,
        status_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List batch jobs for a customer.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            status_filter: Optional status filter

        Returns:
            List of batch jobs
        """
        try:
            customer_id = format_customer_id(customer_id)

            # Use GoogleAdsService for search
            sdk_client = get_sdk_client()
            google_ads_service: GoogleAdsServiceClient = sdk_client.client.get_service(
                "GoogleAdsService"
            )

            # Build query
            query = """
                SELECT
                    batch_job.resource_name,
                    batch_job.id,
                    batch_job.status,
                    batch_job.long_running_operation,
                    batch_job.metadata.creation_date_time,
                    batch_job.metadata.start_date_time,
                    batch_job.metadata.completion_date_time,
                    batch_job.metadata.estimated_completion_ratio,
                    batch_job.metadata.operation_count,
                    batch_job.metadata.executed_operation_count
                FROM batch_job
            """

            if status_filter:
                query += f" WHERE batch_job.status = '{status_filter}'"

            query += " ORDER BY batch_job.metadata.creation_date_time DESC"

            # Execute search
            response = google_ads_service.search(customer_id=customer_id, query=query)

            # Process results
            results = []
            for row in response:
                results.append(serialize_proto_message(row))

            await ctx.log(
                level="info",
                message=f"Found {len(results)} batch jobs",
            )

            return results

        except Exception as e:
            error_msg = f"Failed to list batch jobs: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e


def create_batch_job_tools(
    service: BatchJobService,
) -> List[Callable[..., Awaitable[Any]]]:
    """Create tool functions for the batch job service.

    This returns a list of tool functions that can be registered with FastMCP.
    This approach makes the tools testable by allowing service injection.
    """
    tools = []

    async def create_batch_job(
        ctx: Context,
        customer_id: str,
    ) -> Dict[str, Any]:
        """Create a new batch job for bulk operations.

        Args:
            customer_id: The customer ID

        Returns:
            Created batch job details with resource_name
        """
        return await service.create_batch_job(
            ctx=ctx,
            customer_id=customer_id,
        )

    async def get_batch_job(
        ctx: Context,
        customer_id: str,
        batch_job_resource_name: str,
    ) -> Dict[str, Any]:
        """Get batch job details and status.

        Args:
            customer_id: The customer ID
            batch_job_resource_name: The batch job resource name

        Returns:
            Batch job details including status and metadata
        """
        return await service.get_batch_job(
            ctx=ctx,
            customer_id=customer_id,
            batch_job_resource_name=batch_job_resource_name,
        )

    async def add_operations_to_batch_job(
        ctx: Context,
        customer_id: str,
        batch_job_resource_name: str,
        operations_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Add operations to a batch job for bulk execution.

        Each operation dict must have a "type" and "action" field.
        Supported types and their required fields:

        campaign_budget:
          create: {type, action, name, amount_micros, explicitly_shared?}
          update: {type, action, resource_name, amount_micros?}
          remove: {type, action, resource_name}

        campaign:
          update: {type, action, resource_name, name?, status?}
          remove: {type, action, resource_name}

        ad_group:
          create: {type, action, name, campaign_id, cpc_bid_micros?}
          update: {type, action, resource_name, name?, status?, cpc_bid_micros?}
          remove: {type, action, resource_name}

        ad_group_criterion (or keyword):
          create: {type, action, ad_group_id, text, match_type?}
          remove: {type, action, resource_name}

        Args:
            customer_id: The customer ID
            batch_job_resource_name: The batch job resource name
            operations_data: List of operation dicts as described above

        Returns:
            Result with sequence_token for chaining more add_operations calls
        """
        return await service.add_operations_to_batch_job(
            ctx=ctx,
            customer_id=customer_id,
            batch_job_resource_name=batch_job_resource_name,
            operations_data=operations_data,
        )

    async def run_batch_job(
        ctx: Context,
        customer_id: str,
        batch_job_resource_name: str,
    ) -> Dict[str, Any]:
        """Run a batch job to execute all added operations.

        Args:
            customer_id: The customer ID
            batch_job_resource_name: The batch job resource name

        Returns:
            Batch job execution details with long running operation name
        """
        return await service.run_batch_job(
            ctx=ctx,
            customer_id=customer_id,
            batch_job_resource_name=batch_job_resource_name,
        )

    async def list_batch_job_results(
        ctx: Context,
        customer_id: str,
        batch_job_resource_name: str,
        page_size: int = 1000,
        page_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List batch job results to see success/failure of operations.

        Args:
            customer_id: The customer ID
            batch_job_resource_name: The batch job resource name
            page_size: Number of results per page (max 1000)
            page_token: Token for pagination

        Returns:
            Batch job results with operation status and errors
        """
        return await service.list_batch_job_results(
            ctx=ctx,
            customer_id=customer_id,
            batch_job_resource_name=batch_job_resource_name,
            page_size=page_size,
            page_token=page_token,
        )

    async def list_batch_jobs(
        ctx: Context,
        customer_id: str,
        status_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List batch jobs for a customer.

        Args:
            customer_id: The customer ID
            status_filter: Optional status filter (UNKNOWN, PENDING, RUNNING, DONE)

        Returns:
            List of batch jobs with status and metadata
        """
        return await service.list_batch_jobs(
            ctx=ctx,
            customer_id=customer_id,
            status_filter=status_filter,
        )

    tools.extend(
        [
            create_batch_job,
            get_batch_job,
            add_operations_to_batch_job,
            run_batch_job,
            list_batch_job_results,
            list_batch_jobs,
        ]
    )
    return tools


def register_batch_job_tools(mcp: FastMCP[Any]) -> BatchJobService:
    """Register batch job tools with the MCP server.

    Returns the BatchJobService instance for testing purposes.
    """
    service = BatchJobService()
    tools = create_batch_job_tools(service)

    # Register each tool
    for tool in tools:
        mcp.tool(tool)

    return service
