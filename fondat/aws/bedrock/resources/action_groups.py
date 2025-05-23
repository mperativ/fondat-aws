"""Resource for managing agent action groups."""

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
class ActionGroupsResource:
    """
    Resource for managing agent action groups.
    Provides access to list action groups and retrieve specific action group details.
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
    async def get(
        self,
        agentVersion: str,
        *,
        max_results: int | None = None,
        cursor: Cursor | None = None,
    ) -> Any:
        """
        List all action groups for the agent.

        Args:
            agentVersion: The version of the agent
            max_results: Optional maximum number of results to return
            cursor: Optional pagination cursor

        Returns:
            Page of action group summaries
        """
        params = {"agentId": self._agent_id, "agentVersion": agentVersion}
        if max_results is not None:
            params["maxResults"] = max_results
        if cursor is not None:
            params["nextToken"] = decode_cursor(cursor)
        async with agent_client(self.config_agent) as client:
            resp = await client.list_agent_action_groups(**params)
        return paginate(resp, items_key="actionGroupSummaries")

    @operation(method="get", policies=lambda self: self.policies)
    async def get_action_group(self, actionGroupId: str, agentVersion: str) -> Mapping[str, Any]:
        """
        Retrieve details of a specific action group.

        Args:
            actionGroupId: The identifier of the action group
            agentVersion: The version of the agent

        Returns:
            Mapping containing action group details
        """
        async with agent_client(self.config_agent) as client:
            return await client.get_agent_action_group(
                agentId=self._agent_id,
                actionGroupId=actionGroupId,
                agentVersion=agentVersion
            )
