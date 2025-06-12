"""Root resource for Bedrock agents."""

from collections.abc import Iterable
from typing import Any

from fondat.aws.bedrock.domain import AgentSummary
from fondat.aws.client import Config, wrap_client_error
from fondat.pagination import Cursor, Page
from fondat.resource import resource
from fondat.security import Policy

from ..clients import agent_client
from ..decorators import operation
from ..pagination import decode_cursor, paginate
from ..cache import BedrockCache
from ..utils import parse_bedrock_datetime
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
        cache_size: int = 100,
        cache_expire: int | float = 300,
    ):
        self.config_agent = config_agent
        self.config_runtime = config_runtime
        self.policies = policies
        self._cache = BedrockCache(
            cache_size=cache_size,
            cache_expire=cache_expire,
        )

    async def _list_agents(self, max_results: int | None = None, cursor: Cursor | None = None) -> Page[AgentSummary]:
        """Internal method to list agents without caching."""
        params: dict[str, Any] = {}
        if max_results is not None:
            params["maxResults"] = max_results
        if cursor is not None:
            params["nextToken"] = decode_cursor(cursor)
        async with agent_client(self.config_agent) as client:
            with wrap_client_error():
                resp = await client.list_agents(**params)
        return paginate(
            resp,
            items_key="agentSummaries",
            mapper=lambda d: AgentSummary(
                agent_id=d["agentId"],
                agent_name=d["agentName"],
                status=d["agentStatus"],
                last_updated_at=parse_bedrock_datetime(d.get("lastUpdatedAt")),
                prepared_at=parse_bedrock_datetime(d.get("preparedAt")),
                _factory=lambda aid=d["agentId"], self=self: self[aid],
            ),
        )

    @operation(method="get", policies=lambda self: self.policies)
    async def get(self, *, max_results: int | None = None, cursor: Cursor | None = None) -> Page[AgentSummary]:
        """
        List available Bedrock agents.

        Args:
            max_results: Optional maximum number of results to return
            cursor: Optional pagination cursor

        Returns:
            Page of agent summaries
        """
        # Don't cache if pagination is being used
        if cursor is not None:
            return await self._list_agents(max_results=max_results, cursor=cursor)
            
        # Use cache for first page results
        cache_key = f"agents_list_{max_results}"
        return await self._cache.get_cached_page(
            cache_key=cache_key,
            page_type=Page[AgentSummary],
            fetch_func=self._list_agents,
            max_results=max_results,
        )

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
