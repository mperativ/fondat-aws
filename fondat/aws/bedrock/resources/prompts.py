"""Resource for managing agent prompts."""

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
class PromptsResource:
    """Resource for managing agent prompts."""

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
        *,
        promptIdentifier: str | None = None,
        max_results: int | None = None,
        cursor: Cursor | None = None,
    ) -> Any:
        """List agent prompts.

        Args:
            promptIdentifier: Prompt identifier to list versions for
            max_results: Maximum number of results to return
            cursor: Pagination cursor

        Returns:
            Page of prompt summaries
        """
        params = {}
        if promptIdentifier is not None:
            params["promptIdentifier"] = promptIdentifier
        if max_results is not None:
            params["maxResults"] = max_results
        if cursor is not None:
            params["nextToken"] = decode_cursor(cursor)
        async with agent_client(self.config_agent) as client:
            resp = await client.list_prompts(**params)
        return paginate(resp, items_key="promptSummaries")

    @operation(method="get", policies=lambda self: self.policies)
    async def get_prompt(
        self,
        promptIdentifier: str,
        *,
        promptVersion: str | None = None,
    ) -> Mapping[str, Any]:
        """Get prompt details.

        Args:
            promptIdentifier: Prompt identifier
            promptVersion: Prompt version

        Returns:
            Prompt details
        """
        params = {
            "promptIdentifier": promptIdentifier,
        }
        if promptVersion is not None:
            params["promptVersion"] = promptVersion
        async with agent_client(self.config_agent) as client:
            return await client.get_prompt(**params)
