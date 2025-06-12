from collections.abc import Iterable
from typing import Any, TypeVar, Generic
import json
from datetime import datetime

from fondat.resource import resource
from fondat.security import Policy
from fondat.aws.bedrock.domain import (
    AliasSummary, 
    VersionSummary, 
    AgentVersion,
    FlowVersion,
    PromptVersion,
    AgentAlias,
    FlowAlias
)
from fondat.pagination import Cursor, Page
from ..decorators import operation
from ..clients import agent_client
from ..pagination import decode_cursor, paginate
from ..cache import BedrockCache
from ..utils import parse_bedrock_datetime
from fondat.aws.bedrock.utils import convert_dict_keys_to_snake_case

VT = TypeVar("VT", AgentVersion, FlowVersion, PromptVersion)
AT = TypeVar("AT", AgentAlias, FlowAlias)


@resource
class GenericVersionResource:
    """
    Generic class to handle 'list versions' and 'get version'
    in any resource that follows the AWS Bedrock pattern (agents, flows, or prompts).

    Parameters (in __init__):
        parent_id: identifier of the parent resource (agentId or flowIdentifier).
        id_field: name of the field sent to the client (e.g. "agentId" or "flowIdentifier").
        list_method: name of the botocore method to list versions
                     (e.g.: "list_agent_versions", "list_flow_versions", or "list_prompt_versions").
        get_method: name of the botocore method to get a single version
                     (e.g.: "get_agent_version", "get_flow_version").
        items_key: key in the botocore response that contains the list
                   (e.g.: "agentVersionSummaries", "flowVersionSummaries").
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
                "id": "agent_version",
                "name": "version_name",
                "created_at": "created_at",
                "description": "description",
                "metadata": "metadata",
            }
        elif self.id_field == "flowIdentifier":
            return {
                "id": "id",
                "name": "name",
                "created_at": "created_at",
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
                mapper=lambda d: (
                    lambda d2: VersionSummary(
                        version_id=d2[fields["id"]],
                        version_name=d2.get(fields["name"]),
                        created_at=parse_bedrock_datetime(d2.get(fields["created_at"])),
                        description=d2.get(fields["description"]),
                        _factory=lambda vid=d2[fields["id"]], self=self: self[vid],
                    )
                )(convert_dict_keys_to_snake_case(d)),
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


    def __getitem__(self, version: str) -> "VersionResource[VT]":
        """Get a specific version resource.

        Parameters:
            version: version identifier

        Returns:
            VersionResource instance
        """
        dto_map = {
            "agentId": AgentVersion,
            "flowIdentifier": FlowVersion,
        }
        return VersionResource[VT](
            self._parent_id,
            version,
            id_field=self.id_field,
            get_method=self.get_method,
            dto_type=dto_map[self.id_field],
            config=self.config,
            policies=self.policies,
        )


@resource
class VersionResource(Generic[VT]):
    """Resource for managing a specific version."""

    __slots__ = (
        "_parent_id",
        "_version",
        "id_field",
        "get_method",
        "config",
        "policies",
        "_dto_type",
    )

    # ---------------------------------------
    # Class-level mappings and required fields
    # ---------------------------------------
    FIELD_MAPPINGS: dict[str, dict[str, str]] = {
        "agentId": {
            "arn": "version_arn",
            "id": "version_id",
            "name": "version_name",
            "createdAt": "created_at",
            "updatedAt": "updatedAt",
        },
        "flowIdentifier": {
            "version_arn": "arn",
            "version_id": "id",
            "flow_id": "id",
            "flow_name": "name",
            "created_at": "created_at",
            "flow_version": "version",
            "version": "version",
            "status": "status",
            "definition": "definition",
            "updated_at": "updated_at",
        },
    }

    REQUIRED_FIELDS: dict[str, list[str]] = {
        "agentId": [
            "version_arn",
            "version_id",
            "version_name",
            "created_at",
            "updated_at",
        ],
        "flowIdentifier": [
            "version_arn",
            "version_id",
            "flow_id",
            "flow_name",
            "created_at",
            "flow_version",
            "version",
            "status",
            "definition",
            "updated_at",
        ]
    }

    def __init__(
        self,
        parent_id: str,
        version: str,
        *,
        id_field: str,
        get_method: str,
        dto_type: type[VT],
        config: Any | None = None,
        policies: Iterable[Policy] | None = None,
    ):
        self._parent_id = parent_id
        self._version = version
        self.id_field = id_field
        self.get_method = get_method
        self.config = config
        self.policies = policies
        self._dto_type = dto_type

    def _get_field_mappings(self) -> dict[str, str]:
        return self.FIELD_MAPPINGS[self.id_field]

    def _get_required_fields(self) -> list[str]:
        return self.REQUIRED_FIELDS[self.id_field]

    def _map_response_fields(self, response_data: dict[str, Any]) -> dict[str, Any]:
        """Map response fields according to resource type."""
        mapping = self._get_field_mappings()
        print(f"\nField mappings: {mapping}")
        # map only present fields (dest_field ← response_data[src_field])
        mapped = {
            dest: response_data[src] if src in response_data else None
            for dest, src in mapping.items()
        }
        print(f"\nMapped fields: {mapped}")

        # validate that *destination* keys are all present
        required = self._get_required_fields()
        print(f"\nRequired fields: {required}")
        missing = set(required) - mapped.keys()
        if missing:
            raise ValueError(
                f"Missing required fields for {self.id_field}: {sorted(missing)}"
            )

        # Convert all keys to snake_case
        return convert_dict_keys_to_snake_case(mapped)

    @operation(method="get", policies=lambda self: self.policies)
    async def get(self) -> VT:
        """Get version details."""
        key_for_version = {
            "agentId": "agentVersion",
            "flowIdentifier": "flowVersion",
        }[self.id_field]

        params = {self.id_field: self._parent_id, key_for_version: self._version}
        async with agent_client(self.config) as client:
            response = await getattr(client, self.get_method)(**params)
            data = {k: v for k, v in response.items() if k != "ResponseMetadata"}
            print(f"\nAPI Response data: {data}")
            data = convert_dict_keys_to_snake_case(data)
            print(f"\nAfter snake_case conversion: {data}")
            mapped = self._map_response_fields(data)
            print(f"\nAfter mapping: {mapped}")
            return self._dto_type(**mapped)

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
                "alias_id": "agentAliasId",
                "alias_name": "agentAliasName",
                "created_at": "createdAt",
                "description": "description",
                "metadata": "metadata",
            }
        elif self.id_field == "flowIdentifier":
            return {
                "alias_id": "id",
                "alias_name": "name",
                "created_at": "createdAt",
                "description": "description",
                "routing_configuration": "routingConfiguration",
                "flow_id": "flowId",
                "arn": "arn",
            }

    def _get_dto_type(self) -> type[AT]:
        """Get the DTO type for the current resource type."""
        if self.id_field == "agentId":
            return AgentAlias
        elif self.id_field == "flowIdentifier":
            return FlowAlias
        raise ValueError(f"Unknown id_field: {self.id_field}")

    async def _list_aliases(
        self,
        max_results: int | None = None,
        cursor: Cursor | None = None,
        **kwargs,
    ) -> Page[AliasSummary]:
        """List aliases with pagination."""
        params = {self.id_field: self._parent_id}
        if max_results:
            params["maxResults"] = max_results
        if cursor:
            params["nextToken"] = decode_cursor(cursor)

        async with agent_client(self.config) as client:
            resp = await getattr(client, self.list_method)(**params)
            print(f"\nAPI Response: {resp}")
            field_mapping = self._get_field_mapping()
            print(f"\nField mapping: {field_mapping}")
            return paginate(
                resp=resp,
                items_key=self.items_key,
                mapper=lambda d: AliasSummary(
                    alias_id=d.get(field_mapping["alias_id"]),
                    alias_name=d.get(field_mapping["alias_name"]),
                    created_at=parse_bedrock_datetime(d.get(field_mapping["created_at"])),
                    metadata=d.get(field_mapping.get("metadata")),
                    _factory=lambda aid=d.get(field_mapping["alias_id"]), self=self: self[aid],
                ),
            )

    @operation(method="get", policies=lambda self: self.policies)
    async def get(
        self,
        *,
        max_results: int | None = None,
        cursor: Cursor | None = None,
    ) -> Page[AliasSummary]:
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

    def __getitem__(self, alias_id: str) -> "AliasResource[AT]":
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
            dto_type=self._get_dto_type(),
            config=self.config,
            policies=self.policies,
        )


@resource
class AliasResource(Generic[AT]):
    """Resource for managing a specific alias."""

    __slots__ = ("_parent_id", "_alias_id", "id_field", "get_method", "config", "policies", "_dto_type")

    # ---------------------------------------
    # Class-level mappings and required fields
    # ---------------------------------------
    FIELD_MAPPINGS: dict[str, dict[str, str]] = {
        "agentId": {
            "arn": "agent_alias_arn",
            "agent_alias_id": "agent_alias_id",
            "agent_alias_name": "agent_alias_name",
            "created_at": "created_at",
            "updated_at": "updated_at",
        },
        "flowIdentifier": {
            "arn": "alias_arn",
            "flow_alias_id": "alias_id",
            "flow_alias_name": "alias_name",
            "flow_id": "flow_id",
            "created_at": "created_at",
            "updated_at": "updated_at",
            "concurrency_configuration": "concurrency_configuration",
            "description": "description",
            "routing_configuration": "routing_configuration",
        },
    }

    REQUIRED_FIELDS: dict[str, list[str]] = {
        "agentId": [
            "agent_alias_arn",
            "agent_alias_id",
            "agent_alias_name",
            "created_at",
            "updated_at",
        ],
        "flowIdentifier": [
            "alias_arn",
            "alias_id",
            "alias_name",
            "flow_id",
            "created_at",
            "updated_at",
        ],
    }

    def __init__(
        self,
        parent_id: str,
        alias_id: str,
        *,
        id_field: str,
        get_method: str,
        dto_type: type[AT],
        config: Any | None = None,
        policies: Iterable[Policy] | None = None,
    ):
        self._parent_id = parent_id
        self._alias_id = alias_id
        self.id_field = id_field
        self.get_method = get_method
        self.config = config
        self.policies = policies
        self._dto_type = dto_type

    def _get_field_mappings(self) -> dict[str, str]:
        return self.FIELD_MAPPINGS[self.id_field]

    def _get_required_fields(self) -> list[str]:
        return self.REQUIRED_FIELDS[self.id_field]

    def _map_response_fields(self, response_data: dict[str, Any]) -> dict[str, Any]:
        """Map response fields according to resource type."""
        mapping = self._get_field_mappings()
        # map only present fields (dest_field ← response_data[src_field])
        mapped = {
            dest: response_data[src]
            for dest, src in mapping.items()
            if src in response_data
        }

        # validate that *destination* keys are all present
        required = self._get_required_fields()
        missing = set(required) - mapped.keys()
        if missing:
            raise ValueError(
                f"Missing required fields for {self.id_field}: {sorted(missing)}"
            )

        # Convert all keys to snake_case
        return convert_dict_keys_to_snake_case(mapped)

    @operation(method="get", policies=lambda self: self.policies)
    async def get(self) -> AT:
        """Get alias details."""
        key_for_alias = {
            "agentId": "agentAliasId",
            "flowIdentifier": "aliasIdentifier",
        }[self.id_field]
            
        params = {self.id_field: self._parent_id, key_for_alias: self._alias_id}
        async with agent_client(self.config) as client:
            response = await getattr(client, self.get_method)(**params)
            data = {k: v for k, v in response.items() if k != "ResponseMetadata"}
            mapped = self._map_response_fields(data)
            return self._dto_type(**mapped)
