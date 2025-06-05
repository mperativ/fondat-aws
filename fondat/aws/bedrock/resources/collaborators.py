"""Resource for managing agent collaborators."""

from collections.abc import Iterable

from fondat.aws.client import Config
from fondat.aws.bedrock.domain import AgentCollaborator, AgentCollaboratorSummary
from fondat.pagination import Cursor, Page
from fondat.resource import resource
from fondat.security import Policy

from ..clients import agent_client
from ..decorators import operation
from ..pagination import decode_cursor, paginate
from ..cache import BedrockCache
from ..utils import parse_bedrock_datetime


@resource
class CollaboratorsResource:
    """Resource for managing agent collaborators."""

    __slots__ = ("_agent_id", "config_agent", "policies", "_cache")

    def __init__(
        self,
        agent_id: str,
        *,
        config_agent: Config | None = None,
        policies: Iterable[Policy] | None = None,
        cache_size: int = 100,
        cache_expire: int | float = 300,
    ):
        self._agent_id = agent_id
        self.config_agent = config_agent
        self.policies = policies
        self._cache = BedrockCache(
            cache_size=cache_size,
            cache_expire=cache_expire,
        )

    async def _list_collaborators(
        self,
        max_results: int | None = None,
        cursor: Cursor | None = None,
        agentVersion: str | None = None,
    ) -> Page[AgentCollaboratorSummary]:
        """Internal method to list collaborators without caching."""
        params = {"agentId": self._agent_id}
        if max_results is not None:
            params["maxResults"] = max_results
        if cursor is not None:
            params["nextToken"] = decode_cursor(cursor)
        if agentVersion is not None:
            params["agentVersion"] = agentVersion
        async with agent_client(self.config_agent) as client:
            resp = await client.list_agent_collaborators(**params)
        return paginate(
            resp,
            items_key="agentCollaboratorSummaries",
            mapper=lambda d: AgentCollaboratorSummary(
                agent_id=d["agentId"],
                collaborator_id=d["collaboratorId"],
                collaborator_type=d["collaboratorType"],
                created_at=parse_bedrock_datetime(d["createdAt"]),
            ),
        )

    @operation(method="get", policies=lambda self: self.policies)
    async def get(
        self,
        *,
        max_results: int | None = None,
        cursor: Cursor | None = None,
        agentVersion: str | None = None,
    ) -> Page[AgentCollaboratorSummary]:
        """List agent collaborators.

        Args:
            max_results: Maximum number of results to return
            cursor: Pagination cursor
            agentVersion: Optional agent version

        Returns:
            Page of collaborator summaries
        """
        # Don't cache if pagination is being used
        if cursor is not None:
            return await self._list_collaborators(
                max_results=max_results,
                cursor=cursor,
                agentVersion=agentVersion,
            )
            
        # Use cache for first page results
        cache_key = f"agent_{self._agent_id}_collaborators_{max_results}_{agentVersion}"
        return await self._cache.get_cached_page(
            cache_key=cache_key,
            page_type=Page[AgentCollaboratorSummary],
            fetch_func=self._list_collaborators,
            max_results=max_results,
            agentVersion=agentVersion,
        )

    def __getitem__(self, collaborator_id: str) -> "CollaboratorResource":
        """Get a specific collaborator resource.

        Args:
            collaborator_id: Collaborator identifier

        Returns:
            CollaboratorResource instance
        """
        return CollaboratorResource(
            self._agent_id,
            collaborator_id,
            config_agent=self.config_agent,
            policies=self.policies,
        )


@resource
class CollaboratorResource:
    """Resource for managing a specific collaborator."""

    __slots__ = ("_agent_id", "_collaborator_id", "config_agent", "policies")

    def __init__(
        self,
        agent_id: str,
        collaborator_id: str,
        *,
        config_agent: Config | None = None,
        policies: Iterable[Policy] | None = None,
    ):
        self._agent_id = agent_id
        self._collaborator_id = collaborator_id
        self.config_agent = config_agent
        self.policies = policies

    @operation(method="get", policies=lambda self: self.policies)
    async def get(self, *, agentVersion: str | None = None) -> AgentCollaborator:
        """Get collaborator details.

        Args:
            agentVersion: Optional agent version

        Returns:
            Collaborator details
        """
        params = {
            "agentId": self._agent_id,
            "collaboratorId": self._collaborator_id,
        }
        if agentVersion is not None:
            params["agentVersion"] = agentVersion
        async with agent_client(self.config_agent) as client:
            return await client.get_agent_collaborator(**params)
