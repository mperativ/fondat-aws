"""Resource for managing agent collaborators."""

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
class CollaboratorsResource:
    """
    Resource for managing agent collaborators.
    Provides access to list collaborators for the agent.
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
        """List agent collaborators.

        Args:
            agentVersion: Agent version (pattern: ^(DRAFT|[0-9]{0,4}[1-9][0-9]{0,4})$)
            max_results: Maximum number of results to return
            cursor: Pagination cursor

        Returns:
            Page of collaborator summaries
        """
        params = {
            "agentId": self._agent_id,
            "agentVersion": agentVersion,
        }
        if max_results is not None:
            params["maxResults"] = max_results
        if cursor is not None:
            params["nextToken"] = decode_cursor(cursor)
        async with agent_client(self.config_agent) as client:
            resp = await client.list_agent_collaborators(**params)
        return paginate(resp, items_key="agentCollaboratorSummaries")

    @operation(method="get", policies=lambda self: self.policies)
    async def get_collaborator(
        self,
        collaboratorId: str,
        agentVersion: str,
    ) -> Mapping[str, Any]:
        """Get collaborator details.

        Args:
            collaboratorId: Collaborator identifier
            agentVersion: Agent version

        Returns:
            Collaborator details
        """
        params = {
            "agentId": self._agent_id,
            "agentVersion": agentVersion,
            "collaboratorId": collaboratorId,
        }
        async with agent_client(self.config_agent) as client:
            return await client.get_agent_collaborator(**params)
