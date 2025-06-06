"""Resource for managing agent action groups."""

from collections.abc import Iterable

from fondat.aws.client import Config, wrap_client_error
from fondat.aws.bedrock.domain import ActionGroup, ActionGroupSummary
from fondat.pagination import Cursor, Page
from fondat.resource import resource
from fondat.security import Policy

from ..clients import agent_client
from ..decorators import operation
from ..pagination import decode_cursor, paginate
from ..cache import BedrockCache


@resource
class ActionGroupsResource:
    """
    Resource for managing agent action groups.
    Provides access to list action groups and retrieve specific action group details.
    """

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

    async def _list_action_groups(
        self,
        agentVersion: str,
        max_results: int | None = None,
        cursor: Cursor | None = None,
    ) -> Page[ActionGroupSummary]:
        """Internal method to list action groups without caching."""
        params = {"agentId": self._agent_id, "agentVersion": agentVersion}
        if max_results is not None:
            params["maxResults"] = max_results
        if cursor is not None:
            params["nextToken"] = decode_cursor(cursor)
        async with agent_client(self.config_agent) as client:
            resp = await client.list_agent_action_groups(**params)
        return paginate(
            resp,
            items_key="actionGroupSummaries",
            mapper=lambda d: ActionGroupSummary(
                action_group_id=d["actionGroupId"],
                action_group_name=d["actionGroupName"],
                description=d.get("description"),
                _factory=lambda agid=d["actionGroupId"], self=self: self[agid],
            ),
        )

    @operation(method="get", policies=lambda self: self.policies)
    async def get(
        self,
        agentVersion: str,
        *,
        max_results: int | None = None,
        cursor: Cursor | None = None,
    ) -> Page[ActionGroupSummary]:
        """
        List all action groups for the agent.

        Args:
            agentVersion: The version of the agent
            max_results: Optional maximum number of results to return
            cursor: Optional pagination cursor

        Returns:
            Page of action group summaries
        """
        # Don't cache if pagination is being used
        if cursor is not None:
            return await self._list_action_groups(
                agentVersion=agentVersion,
                max_results=max_results,
                cursor=cursor,
            )
            
        # Use cache for first page results
        cache_key = f"agent_{self._agent_id}_version_{agentVersion}_action_groups_{max_results}"
        return await self._cache.get_cached_page(
            cache_key=cache_key,
            page_type=Page[ActionGroupSummary],
            fetch_func=self._list_action_groups,
            agentVersion=agentVersion,
            max_results=max_results,
        )

    def __getitem__(self, action_group_id: str) -> "ActionGroupResource":
        """Get a specific action group resource.

        Args:
            action_group_id: Action group identifier

        Returns:
            ActionGroupResource instance
        """
        return ActionGroupResource(
            self._agent_id,
            action_group_id,
            config_agent=self.config_agent,
            policies=self.policies,
        )


@resource
class ActionGroupResource:
    """Resource for managing a specific action group."""

    __slots__ = ("_agent_id", "_action_group_id", "config_agent", "policies")

    def __init__(
        self,
        agent_id: str,
        action_group_id: str,
        *,
        config_agent: Config | None = None,
        policies: Iterable[Policy] | None = None,
    ):
        self._agent_id = agent_id
        self._action_group_id = action_group_id
        self.config_agent = config_agent
        self.policies = policies

    @operation(method="get", policies=lambda self: self.policies)
    async def get(self, agentVersion: str) -> ActionGroup:
        """
        Retrieve details of the action group.

        Args:
            agentVersion: The version of the agent

        Returns:
            Mapping containing action group details
        """
        async with agent_client(self.config_agent) as client:
            with wrap_client_error():
                return await client.get_agent_action_group(
                    agentId=self._agent_id,
                    actionGroupId=self._action_group_id,
                    agentVersion=agentVersion
                )
