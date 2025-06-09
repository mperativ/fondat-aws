"""Resource for managing agent memory."""

from collections.abc import Iterable

from fondat.aws.client import Config, wrap_client_error
from fondat.resource import resource
from fondat.security import Policy
from fondat.aws.bedrock.domain import MemorySessionSummary, MemoryContents, MemoryContent, SessionSummary
from fondat.pagination import Cursor, Page

from ..clients import runtime_client
from ..decorators import operation
from ..pagination import decode_cursor, paginate
from ..cache import BedrockCache
from ..utils import parse_bedrock_datetime


@resource
class MemoryResource:
    """
    Resource for managing agent memory.
    Provides access to retrieve and delete agent memory.
    """

    __slots__ = ("_agent_id", "config_runtime", "policies", "_cache")

    def __init__(
        self,
        agent_id: str,
        *,
        config_runtime: Config | None = None,
        policies: Iterable[Policy] | None = None,
        cache_size: int = 100,
        cache_expire: int | float = 300,
    ):
        self._agent_id = agent_id
        self.config_runtime = config_runtime
        self.policies = policies
        self._cache = BedrockCache(
            cache_size=cache_size,
            cache_expire=cache_expire,
        )

    async def _list_memories(
        self,
        max_results: int | None = None,
        cursor: Cursor | None = None,
    ) -> Page[MemorySessionSummary]:
        """Internal method to list memories without caching."""
        params = {"agentId": self._agent_id}
        if max_results is not None:
            params["maxResults"] = max_results
        if cursor is not None:
            params["nextToken"] = decode_cursor(cursor)
        async with runtime_client(self.config_runtime) as client:
            with wrap_client_error():
                resp = await client.list_agent_memory(**params)
        return paginate(
            resp,
            items_key="memorySessionSummaries",
            mapper=lambda d: MemorySessionSummary(
                memory_id=d["memoryId"],
                memory_name=d["memoryName"],
                created_at=parse_bedrock_datetime(d["createdAt"]),
                description=d.get("description"),
                metadata=d.get("metadata"),
                _factory=lambda mid=d["memoryId"], self=self: self[mid],
            ),
        )

    @operation(method="get", policies=lambda self: self.policies)
    async def get(
        self,
        *,
        max_results: int | None = None,
        cursor: Cursor | None = None,
    ) -> Page[MemorySessionSummary]:
        """List agent memory sessions.

        Args:
            max_results: Maximum number of results to return
            cursor: Pagination cursor

        Returns:
            Page of memory session summaries
        """
        # Don't cache if pagination is being used
        if cursor is not None:
            return await self._list_memories(max_results=max_results, cursor=cursor)
            
        # Use cache for first page results
        cache_key = f"agent_{self._agent_id}_memories_{max_results}"
        return await self._cache.get_cached_page(
            cache_key=cache_key,
            page_type=Page[MemorySessionSummary],
            fetch_func=self._list_memories,
            max_results=max_results,
        )

    def __getitem__(self, memory_id: str) -> "MemorySessionResource":
        """Get a specific memory session resource.

        Args:
            memory_id: Memory session identifier

        Returns:
            MemorySessionResource instance
        """
        return MemorySessionResource(
            self._agent_id,
            memory_id,
            config_runtime=self.config_runtime,
            policies=self.policies,
        )


@resource
class MemorySessionResource:
    """Resource for managing a specific memory session."""

    __slots__ = ("_agent_id", "_memory_id", "config_runtime", "policies")

    def __init__(
        self,
        agent_id: str,
        memory_id: str,
        *,
        config_runtime: Config | None = None,
        policies: Iterable[Policy] | None = None,
    ):
        self._agent_id = agent_id
        self._memory_id = memory_id
        self.config_runtime = config_runtime
        self.policies = policies

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
        """
        params = {
            "agentId": self._agent_id,
            "memoryId": self._memory_id,
            "agentAliasId": agentAliasId,
            "memoryType": memoryType,
        }
        if max_items is not None:
            params["maxItems"] = max_items
        if cursor is not None:
            params["nextToken"] = decode_cursor(cursor)
        async with runtime_client(self.config_runtime) as client:
            with wrap_client_error():
                response = await client.get_agent_memory(**params)
                
                # Convert memory contents
                memory_contents = []
                for content in response.get("memoryContents", []):
                    session_summary = content["sessionSummary"]
                    memory_contents.append(
                        MemoryContent(
                            sessionSummary=SessionSummary(
                                memoryId=session_summary["memoryId"],
                                sessionExpiryTime=session_summary["sessionExpiryTime"],
                                sessionId=session_summary["sessionId"],
                                sessionStartTime=session_summary["sessionStartTime"],
                                summaryText=session_summary["summaryText"]
                            )
                        )
                    )
                
                return MemoryContents(
                    memoryContents=memory_contents,
                    nextToken=response.get("nextToken")
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
        params = {
            "agentId": self._agent_id,
            "memoryId": self._memory_id,
            "agentAliasId": agentAliasId,
        }
        if sessionId is not None:
            params["sessionId"] = sessionId
        async with runtime_client(self.config_runtime) as client:
            with wrap_client_error():
                await client.delete_agent_memory(**params)
