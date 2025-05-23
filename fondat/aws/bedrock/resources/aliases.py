"""Resource for managing agent aliases."""

from collections.abc import Iterable
from typing import Any, Mapping

from fondat.aws.client import Config
from fondat.pagination import Cursor
from fondat.resource import resource
from fondat.security import Policy

from ..clients import agent_client
from ..decorators import operation
from ..pagination import decode_cursor, paginate


@resource
class AliasesResource:
    """
    Resource for managing agent aliases.
    Provides access to list aliases and retrieve specific alias details.
    """

    __slots__ = ("_agent_id", "config_agent", "policies")

    def __init__(
        self,
        agent_id: str,
        *,
        config_agent: Config | None = None,
        policies: Iterable[Policy] | None = None,
    ):
        self._agent_id = agent_id
        self.config_agent = config_agent
        self.policies = policies

    @operation(method="get", policies=lambda self: self.policies)
    async def get(self, *, max_results: int | None = None, cursor: Cursor | None = None) -> Any:
        """
        List all aliases for the agent.

        Args:
            max_results: Optional maximum number of results to return
            cursor: Optional pagination cursor

        Returns:
            Page of agent alias summaries
        """
        params = {"agentId": self._agent_id}
        if max_results is not None:
            params["maxResults"] = max_results
        if cursor is not None:
            params["nextToken"] = decode_cursor(cursor)
        async with agent_client(self.config_agent) as client:
            resp = await client.list_agent_aliases(**params)
        return paginate(resp, items_key="agentAliasSummaries")

    @operation(method="get", policies=lambda self: self.policies)
    async def get_alias(self, agentAliasId: str) -> Mapping[str, Any]:
        """
        Retrieve details of a specific agent alias.

        Args:
            agentAliasId: The identifier of the alias

        Returns:
            Mapping containing alias details
        """
        async with agent_client(self.config_agent) as client:
            return await client.get_agent_alias(
                agentId=self._agent_id, agentAliasId=agentAliasId
            )
