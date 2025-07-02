"""Resource for managing agent memory."""

from collections.abc import Iterable
from sqlite3 import Cursor

from fondat.aws.bedrock.pagination import decode_cursor
from fondat.aws.client import Config, wrap_client_error
from fondat.resource import resource
from fondat.security import Policy
from fondat.aws.bedrock.domain import MemoryContent, MemoryContents, SessionSummary
from fondat.error import NotFoundError, ForbiddenError

from ..clients import runtime_client
from ..decorators import operation
from ..cache import BedrockCache
from ..utils import convert_dict_keys_to_snake_case


@resource
class MemoryResource:
    """
    Resource for managing agent memory.
    Provides access to retrieve and delete agent memory.
    """

    __slots__ = ("_agent_id", "_memory_id", "config_runtime", "policies", "_cache")

    def __init__(
        self,
        agent_id: str,
        memory_id: str | None = None,
        *,
        config_runtime: Config | None = None,
        policies: Iterable[Policy] | None = None,
        cache_size: int = 100,
        cache_expire: int | float = 300,
    ):
        self._agent_id = agent_id
        self._memory_id = memory_id
        self.config_runtime = config_runtime
        self.policies = policies
        self._cache = BedrockCache(
            cache_size=cache_size,
            cache_expire=cache_expire,
        )

    def __getitem__(self, memory_id: str) -> "MemoryResource":
        """Get a specific memory resource.

        Args:
            memory_id: Memory session identifier

        Returns:
            MemoryResource instance
        """
        # Create a new instance with the same configuration
        resource = MemoryResource(
            agent_id=self._agent_id,
            memory_id=memory_id,
            config_runtime=self.config_runtime,
            policies=self.policies,
        )
        # Copy the cache from the parent resource
        resource._cache = self._cache
        return resource

    @operation(method="get", policies=lambda self: self.policies)
    async def get(
        self,
        agentAliasId: str,
        memoryType: str,
        *,
        max_items: int | None = None,
        cursor: Cursor | None = None,
    ) -> MemoryContents:
        """Get memory session details.

        Args:
            agentAliasId: Agent alias identifier
            memoryType: Memory type
            max_items: Maximum number of items to return
            cursor: Pagination cursor

        Returns:
            Memory session details

        Raises:
            NotFoundError: If the memory or agent is not found
            ForbiddenError: If access to the memory is forbidden
        """
        if not self._memory_id:
            raise ValueError("Memory ID is required for get operation")

        params = {
            "agentId": self._agent_id,
            "agentAliasId": agentAliasId,
            "memoryType": memoryType,
            "memoryId": self._memory_id,
        }
        if max_items is not None:
            params["maxItems"] = max_items
        if cursor is not None:
            params["nextToken"] = decode_cursor(cursor)

        cache_key = f"memory:{self._agent_id}:{self._memory_id}:{agentAliasId}:{memoryType}"

        async def fetch_memory():
            async with runtime_client(self.config_runtime) as client:
                try:
                    with wrap_client_error():
                        response = await client.get_agent_memory(**params)
                except Exception as e:
                    # Ensure errors are propagated correctly
                    if isinstance(e, (NotFoundError, ForbiddenError)):
                        raise
                    raise e

                # Convert memory contents
                memory_contents = []
                for content in response.get("memoryContents", []):
                    if "sessionSummary" not in content:
                        raise ValueError("Missing 'sessionSummary' in memory content")
                    session_summary = convert_dict_keys_to_snake_case(content["sessionSummary"])
                    memory_contents.append(
                        MemoryContent(
                            session_summary=SessionSummary(**session_summary)
                        )
                    )

                return MemoryContents(
                    memory_contents=memory_contents,
                    next_token=response.get("nextToken"),
                    _factory=lambda self=self: self
                )

        return await self._cache.get_cached_list(
            cache_key=cache_key, item_type=MemoryContents, fetch_func=fetch_memory
        )

    @operation(method="delete", policies=lambda self: self.policies)
    async def delete(
        self,
        agentAliasId: str,
        *,
        sessionId: str | None = None,
    ) -> None:
        """Delete memory session.

        Args:
            agentAliasId: Agent alias identifier
            sessionId: Session identifier
        """
        if not self._memory_id:
            raise ValueError("Memory ID is required for delete operation")

        params = {
            "agentId": self._agent_id,
            "memoryId": self._memory_id,
            "agentAliasId": agentAliasId,
        }
        if sessionId is not None:
            params["sessionId"] = sessionId

        cache_key = f"memory:{self._agent_id}:{self._memory_id}:{agentAliasId}"
        await self._cache.invalidate(cache_key)

        async with runtime_client(self.config_runtime) as client:
            with wrap_client_error():
                await client.delete_agent_memory(**params)
