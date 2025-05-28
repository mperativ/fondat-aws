"""Resource for managing agent flows."""

import json
from collections.abc import Iterable
from typing import Any, Mapping

from fondat.aws.client import Config
from fondat.pagination import Cursor
from fondat.resource import resource
from fondat.security import Policy

from ..clients import agent_client, runtime_client
from ..decorators import operation
from ..pagination import decode_cursor, paginate


@resource
class FlowsResource:
    """
    Resource for managing agent flows.
    Provides access to list flows, flow aliases, flow versions, and flow operations.
    """

    __slots__ = ("_agent_id", "config_agent", "config_runtime", "policies")

    def __init__(
        self,
        agent_id: str,
        *,
        config_agent: Config | None = None,
        config_runtime: Config | None = None,
        policies: Iterable[Policy] | None = None,
    ):
        self._agent_id = agent_id
        self.config_agent = config_agent
        self.config_runtime = config_runtime
        self.policies = policies

    @operation(method="get", policies=lambda self: self.policies)
    async def get(self, *, max_results: int | None = None, cursor: Cursor | None = None) -> Any:
        """
        List all flows for the agent.

        Args:
            max_results: Optional maximum number of results to return
            cursor: Optional pagination cursor

        Returns:
            Page of flow summaries
        """
        params: dict[str, Any] = {}
        if max_results is not None:
            params["maxResults"] = max_results
        if cursor is not None:
            params["nextToken"] = decode_cursor(cursor)
        async with agent_client(self.config_agent) as client:
            resp = await client.list_flows(**params)
        return paginate(resp, items_key="flowSummaries")

    @operation(method="get", policies=lambda self: self.policies)
    async def list_flow_aliases(
        self,
        flowIdentifier: str,
        *,
        max_results: int | None = None,
        cursor: Cursor | None = None,
    ) -> Any:
        """
        List all aliases for a specific flow.

        Args:
            flowIdentifier: The identifier of the flow
            max_results: Optional maximum number of results to return
            cursor: Optional pagination cursor

        Returns:
            Page of flow alias summaries
        """
        params = {"flowIdentifier": flowIdentifier}
        if max_results is not None:
            params["maxResults"] = max_results
        if cursor is not None:
            params["nextToken"] = decode_cursor(cursor)
        async with agent_client(self.config_agent) as client:
            resp = await client.list_flow_aliases(**params)
        return paginate(resp, items_key="flowAliasSummaries")

    @operation(method="get", policies=lambda self: self.policies)
    async def list_flow_versions(
        self,
        flowIdentifier: str,
        *,
        max_results: int | None = None,
        cursor: Cursor | None = None,
    ) -> Any:
        """
        List all versions for a specific flow.

        Args:
            flowIdentifier: The identifier of the flow
            max_results: Optional maximum number of results to return
            cursor: Optional pagination cursor

        Returns:
            Page of flow version summaries
        """
        params = {"flowIdentifier": flowIdentifier}
        if max_results is not None:
            params["maxResults"] = max_results
        if cursor is not None:
            params["nextToken"] = decode_cursor(cursor)
        async with agent_client(self.config_agent) as client:
            resp = await client.list_flow_versions(**params)
        return paginate(resp, items_key="flowVersionSummaries")

    @operation(method="get", policies=lambda self: self.policies)
    async def get_flow(self, flowIdentifier: str) -> Mapping[str, Any]:
        """
        Retrieve details of a specific flow.

        Args:
            flowIdentifier: The identifier of the flow

        Returns:
            Mapping containing flow details
        """
        async with agent_client(self.config_agent) as client:
            return await client.get_flow(flowIdentifier=flowIdentifier)

    @operation(method="get", policies=lambda self: self.policies)
    async def get_flow_alias(
        self, flowIdentifier: str, aliasIdentifier: str
    ) -> Mapping[str, Any]:
        """
        Retrieve details of a specific flow alias.

        Args:
            flowIdentifier: The identifier of the flow
            aliasIdentifier: The identifier of the alias

        Returns:
            Mapping containing flow alias details
        """
        async with agent_client(self.config_agent) as client:
            return await client.get_flow_alias(
                flowIdentifier=flowIdentifier, aliasIdentifier=aliasIdentifier
            )

    @operation(method="get", policies=lambda self: self.policies)
    async def get_flow_version(
        self, flowIdentifier: str, flowVersion: str
    ) -> Mapping[str, Any]:
        """
        Retrieve details of a specific flow version.

        Args:
            flowIdentifier: The identifier of the flow
            flowVersion: The version identifier

        Returns:
            Mapping containing flow version details
        """
        async with agent_client(self.config_agent) as client:
            return await client.get_flow_version(
                flowIdentifier=flowIdentifier, flowVersion=flowVersion
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
    ) -> Mapping[str, Any]:
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
            Mapping containing flow invocation results
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
            return await client.invoke_flow(**params)
