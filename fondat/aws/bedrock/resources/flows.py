"""Resource for managing agent flows."""

import json
from collections.abc import Iterable

from fondat.aws.client import Config, wrap_client_error
from fondat.aws.bedrock.domain import Flow, FlowInvocation, FlowSummary
from fondat.pagination import Cursor, Page
from fondat.resource import resource
from fondat.security import Policy

from ..clients import agent_client, runtime_client
from ..decorators import operation
from ..pagination import decode_cursor
from .generic_resources import GenericVersionResource, GenericAliasResource
from ..cache import BedrockCache

__all__ = ["FlowsResource", "FlowResource"]


@resource
class FlowsResource:
    """
    Resource for managing agent flows.
    """

    __slots__ = ("_agent_id", "config_agent", "config_runtime", "policies", "_cache")

    def __init__(
        self,
        agent_id: str,
        *,
        config_agent: Config | None = None,
        config_runtime: Config | None = None,
        policies: Iterable[Policy] | None = None,
        cache_size: int = 100,
        cache_expire: int | float = 300,
    ):
        self._agent_id = agent_id
        self.config_agent = config_agent
        self.config_runtime = config_runtime
        self.policies = policies
        self._cache = BedrockCache(
            cache_size=cache_size,
            cache_expire=cache_expire,
        )

    async def _list_flows(
        self,
        max_results: int | None = None,
        cursor: Cursor | None = None,
    ) -> Page[FlowSummary]:
        """Internal method to list flows without caching."""
        params = {}
        if max_results is not None:
            params["maxResults"] = max_results
        if cursor is not None:
            params["nextToken"] = decode_cursor(cursor)
        async with agent_client(self.config_agent) as client:
            resp = await client.list_flows(**params)
            items = [
                FlowSummary(
                    flow_id=item["id"],
                    flow_name=item["name"],
                    status=item["status"],
                    created_at=item["createdAt"],
                    description=item.get("description"),
                    _factory=lambda fid=item["id"], self=self: self[fid],
                )
                for item in resp.get("flowSummaries", [])
            ]
            return Page(
                items=items,
                cursor=resp.get("nextToken"),
            )

    @operation(method="get", policies=lambda self: self.policies)
    async def get(
        self,
        *,
        max_results: int | None = None,
        cursor: Cursor | None = None,
    ) -> Page[FlowSummary]:
        """List agent flows.

        Args:
            max_results: Maximum number of results to return
            cursor: Pagination cursor

        Returns:
            Page of flow summaries
        """
        # Don't cache if pagination is being used
        if cursor is not None:
            return await self._list_flows(max_results=max_results, cursor=cursor)
            
        # Use cache for first page results
        cache_key = f"agent_{self._agent_id}_flows_{max_results}"
        return await self._cache.get_cached_page(
            cache_key=cache_key,
            page_type=Page[FlowSummary],
            fetch_func=self._list_flows,
            max_results=max_results,
        )

    def __getitem__(self, flow_id: str) -> "FlowResource":
        """
        Get a specific flow resource by ID.

        Args:
            flow_id: The identifier of the flow

        Returns:
            FlowResource instance
        """
        return FlowResource(
            self._agent_id,
            flow_id,
            config_agent=self.config_agent,
            config_runtime=self.config_runtime,
            policies=self.policies,
        )


@resource
class FlowResource:
    """
    Resource for managing a specific flow.
    Provides access to flow invocation and runtime operations.
    """

    __slots__ = ("_agent_id", "_flow_id", "config_agent", "config_runtime", "policies")

    def __init__(
        self,
        agent_id: str,
        flow_id: str,
        *,
        config_agent: Config | None = None,
        config_runtime: Config | None = None,
        policies: Iterable[Policy] | None = None,
    ):
        self._agent_id = agent_id
        self._flow_id = flow_id
        self.config_agent = config_agent
        self.config_runtime = config_runtime
        self.policies = policies

    @operation(method="get", policies=lambda self: self.policies)
    async def get(self) -> Flow:
        """
        Retrieve details of this flow.

        Returns:
            Flow: Details of the flow
        """
        async with agent_client(self.config_agent) as client:
            with wrap_client_error():
                response = await client.get_flow(flowIdentifier=self._flow_id)
                return Flow(**response)

    @property
    def versions(self) -> GenericVersionResource:
        """
        Returns a GenericVersionResource configured for flow versions.
        - flow_id: parent_id (flowIdentifier)
        - id_field: "flowIdentifier"
        - list_method: "list_flow_versions"
        - get_method: "get_flow_version"
        - items_key: "flowVersionSummaries"
        """
        return GenericVersionResource(
            parent_id=self._flow_id,
            id_field="flowIdentifier",
            list_method="list_flow_versions",
            get_method="get_flow_version",
            items_key="flowVersionSummaries",
            config=self.config_agent,
            policies=self.policies,
        )

    @property
    def aliases(self) -> GenericAliasResource:
        """
        Returns a GenericAliasResource configured for flow aliases.
        - flow_id: parent_id (flowIdentifier)
        - id_field: "flowIdentifier"
        - list_method: "list_flow_aliases"
        - get_method: "get_flow_alias"
        - items_key: "flowAliasSummaries"
        """
        return GenericAliasResource(
            parent_id=self._flow_id,
            id_field="flowIdentifier",
            list_method="list_flow_aliases",
            get_method="get_flow_alias",
            items_key="flowAliasSummaries",
            config=self.config_agent,
            policies=self.policies,
        )

    @operation(method="post", policies=lambda self: self.policies)
    async def invoke(
        self,
        input_content: str | dict,
        flowAliasIdentifier: str,
        *,
        nodeName: str = "input",
        nodeInputName: str | None = None,
        nodeOutputName: str | None = None,
        enableTrace: bool = False,
        executionId: str | None = None,
        modelPerformanceConfiguration: dict | None = None,
    ) -> FlowInvocation:
        """
        Invoke the flow with the given input.

        Args:
            input_content: The input content to process. Can be:
                - A string for text input
                - A dictionary for JSON input (will be converted to string)
            flowAliasIdentifier: The unique identifier of the flow alias
            nodeName: Optional name of the node to start from. Defaults to "input"
            nodeInputName: Optional name of the node input
            nodeOutputName: Optional name of the node output
            enableTrace: Whether to enable trace information
            executionId: Optional execution identifier
            modelPerformanceConfiguration: Optional model performance configuration

        Returns:
            FlowInvocation: Information about the flow invocation
        """
        str_content = input_content if isinstance(input_content, str) else json.dumps(input_content)

        params = {
            "flowIdentifier": self._flow_id,
            "flowAliasIdentifier": flowAliasIdentifier,
            "inputs": [
                {
                    "nodeName": nodeName,
                    "content": {
                        "document": str_content
                    }
                }
            ],
            "enableTrace": enableTrace,
        }
        if nodeInputName is not None:
            params["inputs"][0]["nodeInputName"] = nodeInputName
        if nodeOutputName is not None:
            params["inputs"][0]["nodeOutputName"] = nodeOutputName
        if executionId is not None:
            params["executionId"] = executionId
        if modelPerformanceConfiguration is not None:
            params["modelPerformanceConfiguration"] = {
                "performanceConfig": modelPerformanceConfiguration
            }
        async with runtime_client(self.config_runtime) as client:
            with wrap_client_error():
                response = await client.invoke_flow(**params)
                return FlowInvocation(**response)
