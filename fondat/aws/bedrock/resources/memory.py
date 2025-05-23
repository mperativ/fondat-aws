"""Resource for managing agent memory."""

from collections.abc import Iterable
from typing import Any, Mapping

from fondat.aws.client import Config
from fondat.resource import resource
from fondat.security import Policy

from ..clients import runtime_client
from ..decorators import operation


@resource
class MemoryResource:
    """
    Resource for managing agent memory.
    Provides access to retrieve and delete agent memory.
    """

    __slots__ = ("_agent_id", "config_runtime", "policies")

    def __init__(
        self,
        agent_id: str,
        *,
        config_runtime: Config | None = None,
        policies: Iterable[Policy] | None = None,
    ):
        self._agent_id = agent_id
        self.config_runtime = config_runtime
        self.policies = policies

    @operation(method="get", policies=lambda self: self.policies)
    async def get(
        self,
        memoryId: str,
        agentAliasId: str,
        memoryType: str,
        *,
        max_items: int | None = None,
        cursor: str | None = None,
    ) -> Mapping[str, Any]:
        """Get agent memory sessions.

        Args:
            memoryId: Memory identifier
            agentAliasId: Agent alias identifier
            memoryType: Memory type
            max_items: Maximum number of items to return
            cursor: Pagination cursor

        Returns:
            Memory contents and pagination token
        """
        params = {
            "agentId": self._agent_id,
            "memoryId": memoryId,
            "agentAliasId": agentAliasId,
            "memoryType": memoryType,
        }
        if max_items is not None:
            params["maxItems"] = max_items
        if cursor is not None:
            params["nextToken"] = cursor
        async with runtime_client(self.config_runtime) as client:
            return await client.get_agent_memory(**params)

    @operation(method="delete", policies=lambda self: self.policies)
    async def delete(
        self,
        memoryId: str,
        agentAliasId: str,
        *,
        sessionId: str | None = None,
    ) -> None:
        """Delete agent memory.

        Args:
            memoryId: Memory identifier
            agentAliasId: Agent alias identifier
            sessionId: Session identifier
        """
        params = {
            "agentId": self._agent_id,
            "memoryId": memoryId,
            "agentAliasId": agentAliasId,
        }
        if sessionId is not None:
            params["sessionId"] = sessionId
        async with runtime_client(self.config_runtime) as client:
            await client.delete_agent_memory(**params)
