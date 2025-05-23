"""Root resource for Bedrock agents."""

from collections.abc import Iterable
from typing import Any

from fondat.aws.client import Config, wrap_client_error
from fondat.pagination import Cursor
from fondat.resource import resource
from fondat.security import Policy

from ..clients import agent_client
from ..decorators import operation
from ..pagination import decode_cursor, paginate
from .agent import AgentResource


@resource
class AgentsResource:
    """
    Resource for listing all Bedrock agents and accessing specific ones.
    """

    def __init__(
        self,
        *,
        config_agent: Config | None = None,
        config_runtime: Config | None = None,
        policies: Iterable[Policy] | None = None,
    ):
        self.config_agent = config_agent
        self.config_runtime = config_runtime
        self.policies = policies

    @operation(method="get", policies=lambda self: self.policies)
    async def get(self, *, max_results: int | None = None, cursor: Cursor | None = None) -> Any:
        """
        List available Bedrock agents.

        Args:
            max_results: Optional maximum number of results to return
            cursor: Optional pagination cursor

        Returns:
            Page of agent summaries
        """
        params: dict[str, Any] = {}
        if max_results is not None:
            params["maxResults"] = max_results
        if cursor is not None:
            params["nextToken"] = decode_cursor(cursor)
        async with agent_client(self.config_agent) as client:
            with wrap_client_error():
                resp = await client.list_agents(**params)
        return paginate(resp, items_key="agentSummaries")

    def __getitem__(self, agent_id: str) -> AgentResource:
        """
        Retrieve a specific agent resource by its ID.

        Args:
            agent_id: The identifier of the agent

        Returns:
            An AgentResource instance
        """
        return AgentResource(
            agent_id=agent_id,
            config_agent=self.config_agent,
            config_runtime=self.config_runtime,
            policies=self.policies,
        )
