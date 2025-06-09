"""Resource for managing agent prompts."""

from collections.abc import Iterable

from fondat.aws.client import Config, wrap_client_error
from fondat.aws.bedrock.domain import Prompt, PromptSummary
from fondat.pagination import Cursor, Page
from fondat.resource import resource
from fondat.security import Policy

from ..clients import agent_client
from ..decorators import operation
from ..pagination import decode_cursor, paginate
from ..cache import BedrockCache
from ..utils import parse_bedrock_datetime
from .generic_resources import GenericVersionResource


@resource
class PromptsResource:
    """Resource for managing agent prompts."""

    __slots__ = ("config_agent", "policies", "_cache")

    def __init__(
        self,
        *,
        config_agent: Config | None = None,
        policies: Iterable[Policy] | None = None,
        cache_size: int = 100,
        cache_expire: int | float = 300,
    ):
        self.config_agent = config_agent
        self.policies = policies
        self._cache = BedrockCache(
            cache_size=cache_size,
            cache_expire=cache_expire,
        )

    async def _list_prompts(
        self,
        max_results: int | None = None,
        cursor: Cursor | None = None,
    ) -> Page[PromptSummary]:
        """Internal method to list prompts without caching."""
        params = {}
        if max_results is not None:
            params["maxResults"] = max_results
        if cursor is not None:
            params["nextToken"] = decode_cursor(cursor)
        async with agent_client(self.config_agent) as client:
            resp = await client.list_prompts(**params)
        return paginate(
            resp,
            items_key="promptSummaries",
            mapper=lambda d: PromptSummary(
                prompt_id=d.get("promptId") or d.get("id"),
                prompt_name=d.get("promptName") or d.get("name"),
                description=d.get("description"),
                created_at=parse_bedrock_datetime(d.get("createdAt") or d.get("created_at")),
                _factory=lambda pid=d.get("promptId") or d.get("id"), self=self: self[pid],
            ),
        )

    @operation(method="get", policies=lambda self: self.policies)
    async def get(
        self,
        *,
        max_results: int | None = None,
        cursor: Cursor | None = None,
    ) -> Page[PromptSummary]:
        """List agent prompts.

        Args:
            max_results: Maximum number of results to return
            cursor: Pagination cursor

        Returns:
            Page of prompt summaries
        """
        # Don't cache if pagination is being used
        if cursor is not None:
            return await self._list_prompts(max_results=max_results, cursor=cursor)
            
        # Use cache for first page results
        cache_key = f"prompts_list_{max_results}"
        return await self._cache.get_cached_page(
            cache_key=cache_key,
            page_type=Page[PromptSummary],
            fetch_func=self._list_prompts,
            max_results=max_results,
        )

    def __getitem__(self, prompt_id: str) -> "PromptResource":
        """Get a specific prompt resource.

        Args:
            prompt_id: Prompt identifier

        Returns:
            PromptResource instance
        """
        return PromptResource(
            prompt_id,
            config_agent=self.config_agent,
            policies=self.policies,
        )


@resource
class PromptResource:
    """Resource for managing a specific prompt."""

    __slots__ = ("_id", "config_agent", "policies")

    def __init__(
        self,
        prompt_id: str,
        *,
        config_agent: Config | None = None,
        policies: Iterable[Policy] | None = None,
    ):
        self._id = prompt_id
        self.config_agent = config_agent
        self.policies = policies

    @operation(method="get", policies=lambda self: self.policies)
    async def get(
        self,
        *,
        promptVersion: str | None = None,
    ) -> Prompt:
        """Get prompt details.

        Args:
            promptVersion: Prompt version

        Returns:
            Prompt details
        """
        params = {
            "promptIdentifier": self._id,
        }
        if promptVersion is not None:
            params["promptVersion"] = promptVersion
        async with agent_client(self.config_agent) as client:
            with wrap_client_error():
                response = await client.get_prompt(**params)
                return Prompt(**response)

    @property
    def versions(self) -> GenericVersionResource:
        """
        Returns a GenericVersionResource configured for prompt versions.
        - prompt_id: parent_id (promptIdentifier)
        - id_field: "promptIdentifier"
        - list_method: "list_prompt_versions"
        - get_method: "get_prompt_version"
        - items_key: "promptVersionSummaries"
        """
        return GenericVersionResource(
            parent_id=self._id,
            id_field="promptIdentifier",
            list_method="list_prompt_versions",
            get_method="get_prompt_version",
            items_key="promptVersionSummaries",
            config=self.config_agent,
            policies=self.policies,
        )
