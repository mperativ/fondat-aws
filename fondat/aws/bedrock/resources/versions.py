"""Resource for managing agent versions."""

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
class VersionsResource:
    """
    Resource for managing agent versions.
    Provides access to list versions and retrieve specific version details.
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
        List all versions of the agent.

        Args:
            max_results: Optional maximum number of results to return
            cursor: Optional pagination cursor

        Returns:
            Page of agent version summaries
        """
        params = {"agentId": self._agent_id}
        if max_results is not None:
            params["maxResults"] = max_results
        if cursor is not None:
            params["nextToken"] = decode_cursor(cursor)
        async with agent_client(self.config_agent) as client:
            resp = await client.list_agent_versions(**params)
        return paginate(resp, items_key="agentVersionSummaries")

    @operation(method="get", policies=lambda self: self.policies)
    async def get_version(self, agentVersion: str) -> Mapping[str, Any]:
        """
        Retrieve details of a specific agent version.

        Args:
            agentVersion: The version identifier of the agent

        Returns:
            Mapping containing version details
        """
        async with agent_client(self.config_agent) as client:
            return await client.get_agent_version(
                agentId=self._agent_id, agentVersion=agentVersion
            )
