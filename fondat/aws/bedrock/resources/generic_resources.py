from collections.abc import Iterable
from typing import Any

from fondat.resource import resource
from fondat.security import Policy
from fondat.aws.bedrock.domain import Alias, AliasSummary, VersionSummary, Version
from fondat.pagination import Cursor, Page
from ..decorators import operation
from ..clients import agent_client
from ..pagination import decode_cursor, paginate
from ..cache import BedrockCache
from ..utils import parse_bedrock_datetime


@resource
class GenericVersionResource:
    """
    Generic class to handle 'list versions' and 'get version'
    in any resource that follows the AWS Bedrock pattern (agents, flows, or prompts).

    Parameters (in __init__):
        parent_id: identifier of the parent resource (agentId, flowIdentifier, or promptIdentifier).
        id_field: name of the field sent to the client (e.g. "agentId", "flowIdentifier", or "promptIdentifier").
        list_method: name of the botocore method to list versions
                     (e.g.: "list_agent_versions", "list_flow_versions", or "list_prompt_versions").
        get_method: name of the botocore method to get a single version
                     (e.g.: "get_agent_version", "get_flow_version", or "get_prompt_version").
        items_key: key in the botocore response that contains the list
                   (e.g.: "agentVersionSummaries", "flowVersionSummaries", or "promptVersionSummaries").
        config: AWS configuration (fondat.aws.client.Config), optional.
        policies: Collection of security policies, optional.
        cache_size: Maximum number of items to cache
        cache_expire: Cache expiration time in seconds
    """

    __slots__ = (
        "_parent_id",
        "id_field",
        "list_method",
        "get_method",
        "items_key",
        "config",
        "policies",
        "_cache",
    )

    def __init__(
        self,
        parent_id: str,
        *,
        id_field: str,
        list_method: str,
        get_method: str,
        items_key: str,
        config: Any | None = None,
        policies: Iterable[Policy] | None = None,
        cache_size: int = 100,
        cache_expire: int | float = 300,
    ):
        self._parent_id = parent_id
        self.id_field = id_field
        self.list_method = list_method
        self.get_method = get_method
        self.items_key = items_key
        self.config = config
        self.policies = policies
        self._cache = BedrockCache(
            cache_size=cache_size,
            cache_expire=cache_expire,
        )

    def _get_field_mapping(self) -> dict[str, str]:
        """Get the field mapping for the current resource type."""
        if self.id_field == "agentId":
            return {
                "id": "agentVersion",
                "name": "versionName",
                "created_at": "createdAt",
                "description": "description",
                "metadata": "metadata",
            }
        elif self.id_field == "flowIdentifier":
            return {
                "id": "flowVersion",
                "name": "versionName",
                "created_at": "createdAt",
                "description": "description",
                "metadata": "metadata",
            }
        elif self.id_field == "promptIdentifier":
            return {
                "id": "promptVersion",
                "name": "versionName",
                "created_at": "createdAt",
                "description": "description",
                "metadata": "metadata",
            }

    async def _list_versions(
        self,
        max_results: int | None = None,
        cursor: Cursor | None = None,
        **kwargs,
    ) -> Page[VersionSummary]:
        """Internal method to list versions without caching."""
        params: dict[str, Any] = {self.id_field: self._parent_id}
        if max_results is not None:
            params["maxResults"] = max_results
        if cursor is not None:
            params["nextToken"] = decode_cursor(cursor)

        async with agent_client(self.config) as client:
            resp = await getattr(client, self.list_method)(**params)
            fields = self._get_field_mapping()
            return paginate(
                resp=resp,
                items_key=self.items_key,
                mapper=lambda d: VersionSummary(
                    version_id=d[fields["id"]],
                    version_name=d.get(fields["name"]),
                    created_at=parse_bedrock_datetime(d[fields["created_at"]]),
                    description=d.get(fields["description"]),
                    metadata=d.get(fields["metadata"]),
                ),
            )

    @operation(method="get", policies=lambda self: self.policies)
    async def get(
        self, *, max_results: int | None = None, cursor: Cursor | None = None
    ) -> Page[VersionSummary]:
        """
        List versions of the parent resource.

        Args:
            max_results: maximum number of results to return (optional).
            cursor: pagination cursor (optional).
        Returns:
            Page with items (each item is a version summary).
        """
        # Don't cache if pagination is being used
        if cursor is not None:
            return await self._list_versions(max_results=max_results, cursor=cursor)
            
        # Use cache for first page results
        cache_key = f"{self.id_field}_{self._parent_id}_versions_{max_results}"
        return await self._cache.get_cached_page(
            cache_key=cache_key,
            page_type=Page[VersionSummary],
            fetch_func=self._list_versions,
            max_results=max_results,
        )


    def __getitem__(self, version: str) -> "VersionResource":
        """Get a specific version resource.

        Args:
            version: Version identifier

        Returns:
            VersionResource instance
        """
        return VersionResource(
            self._parent_id,
            version,
            id_field=self.id_field,
            get_method=self.get_method,
            config=self.config,
            policies=self.policies,
        )


@resource
class VersionResource:
    """Resource for managing a specific version."""

    __slots__ = ("_parent_id", "_version", "id_field", "get_method", "config", "policies")

    def __init__(
        self,
        parent_id: str,
        version: str,
        *,
        id_field: str,
        get_method: str,
        config: Any | None = None,
        policies: Iterable[Policy] | None = None,
    ):
        self._parent_id = parent_id
        self._version = version
        self.id_field = id_field
        self.get_method = get_method
        self.config = config
        self.policies = policies

    @operation(method="get", policies=lambda self: self.policies)
    async def get(self) -> Version:
        """Get version details.

        Returns:
            Version details
        """
        key_for_version = {
            "agentId": "agentVersion",
            "flowIdentifier": "flowVersion",
            "promptIdentifier": "promptVersion",
        }[self.id_field]
        
        params = {self.id_field: self._parent_id, key_for_version: self._version}
        async with agent_client(self.config) as client:
            return await getattr(client, self.get_method)(**params)


@resource
class GenericAliasResource:
    """
    Generic class to handle 'list aliases' and 'get alias'
    in any resource that follows the AWS Bedrock pattern (agents or flows).

    Parameters (in __init__):
        parent_id: identifier of the parent resource (agentId or flowIdentifier).
        id_field: name of the field sent to the client (e.g. "agentId" or "flowIdentifier").
        list_method: name of the botocore method to list aliases
                     (e.g.: "list_agent_aliases" or "list_flow_aliases").
        get_method: name of the botocore method to get a single alias
                     (e.g.: "get_agent_alias" or "get_flow_alias").
        items_key: key in the botocore response that contains the list
                   (e.g.: "agentAliasSummaries" or "flowAliasSummaries").
        config: AWS configuration (fondat.aws.client.Config), optional.
        policies: Collection of security policies, optional.
        cache_size: Maximum number of items to cache
        cache_expire: Cache expiration time in seconds
    """

    __slots__ = (
        "_parent_id",
        "id_field",
        "list_method",
        "get_method",
        "items_key",
        "config",
        "policies",
        "_cache",
    )

    def __init__(
        self,
        parent_id: str,
        *,
        id_field: str,
        list_method: str,
        get_method: str,
        items_key: str,
        config: Any | None = None,
        policies: Iterable[Policy] | None = None,
        cache_size: int = 100,
        cache_expire: int | float = 300,
    ):
        self._parent_id = parent_id
        self.id_field = id_field
        self.list_method = list_method
        self.get_method = get_method
        self.items_key = items_key
        self.config = config
        self.policies = policies
        self._cache = BedrockCache(
            cache_size=cache_size,
            cache_expire=cache_expire,
        )

    def _get_field_mapping(self) -> dict[str, str]:
        """Get the field mapping for the current resource type."""
        if self.id_field == "agentId":
            return {
                "id": "aliasId",
                "name": "aliasName",
                "created_at": "createdAt",
                "description": "description",
                "metadata": "metadata",
            }
        elif self.id_field == "flowIdentifier":
            return {
                "id": "aliasIdentifier",
                "name": "aliasName",
                "created_at": "createdAt",
                "description": "description",
                "metadata": "metadata",
            }

    async def _list_aliases(
        self, max_results: int | None = None, next_token: str | None = None
    ) -> Page[AliasSummary]:
        """List aliases with pagination."""
        params = {self.id_field: self._parent_id}
        if max_results:
            params["maxResults"] = max_results
        if next_token:
            params["nextToken"] = next_token

        async with agent_client(self.config) as client:
            resp = await getattr(client, self.list_method)(**params)
            fields = self._get_field_mapping()
            return paginate(
                resp=resp,
                items_key=self.items_key,
                mapper=lambda d: AliasSummary(
                    alias_id=d[fields["id"]],
                    alias_name=d[fields["name"]],
                    created_at=parse_bedrock_datetime(d[fields["created_at"]]),
                    description=d.get(fields["description"]),
                    metadata=d.get(fields["metadata"]),
                ),
            )

    @operation(method="get", policies=lambda self: self.policies)
    async def get(self, *, max_results: int | None = None, cursor: Cursor | None = None) -> Page[AliasSummary]:
        """
        List aliases of the parent resource.

        Args:
            max_results: maximum number of results to return (optional).
            cursor: pagination cursor (optional).
        Returns:
            Page with items (each item is an alias summary).
        """
        # Don't cache if pagination is being used
        if cursor is not None:
            return await self._list_aliases(max_results=max_results, cursor=cursor)
            
        # Use cache for first page results
        cache_key = f"{self.id_field}_{self._parent_id}_aliases_{max_results}"
        return await self._cache.get_cached_page(
            cache_key=cache_key,
            page_type=Page[AliasSummary],
            fetch_func=self._list_aliases,
            max_results=max_results,
        )

    def __getitem__(self, alias_id: str) -> "AliasResource":
        """Get a specific alias resource.

        Args:
            alias_id: Alias identifier

        Returns:
            AliasResource instance
        """
        return AliasResource(
            self._parent_id,
            alias_id,
            id_field=self.id_field,
            get_method=self.get_method,
            config=self.config,
            policies=self.policies,
        )


@resource
class AliasResource:
    """Resource for managing a specific alias."""

    __slots__ = ("_parent_id", "_alias_id", "id_field", "get_method", "config", "policies")

    def __init__(
        self,
        parent_id: str,
        alias_id: str,
        *,
        id_field: str,
        get_method: str,
        config: Any | None = None,
        policies: Iterable[Policy] | None = None,
    ):
        self._parent_id = parent_id
        self._alias_id = alias_id
        self.id_field = id_field
        self.get_method = get_method
        self.config = config
        self.policies = policies

    @operation(method="get", policies=lambda self: self.policies)
    async def get(self) -> Alias:
        """Get alias details.

        Returns:
            Alias details
        """
        # For flows, the parameter is called "aliasIdentifier" instead of "flowAliasId"
        if self.id_field == "flowIdentifier":
            alias_field = "aliasIdentifier"
        else:
            alias_field = f"{self.id_field[:-2]}AliasId"
            
        params = {self.id_field: self._parent_id, alias_field: self._alias_id}
        async with agent_client(self.config) as client:
            return await getattr(client, self.get_method)(**params)
