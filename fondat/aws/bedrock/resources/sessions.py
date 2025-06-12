"""Resource for managing agent sessions."""

from collections.abc import Iterable
from typing import Any
from datetime import datetime, timezone

from fondat.aws.client import Config, wrap_client_error
from fondat.resource import resource
from fondat.security import Policy
from fondat.aws.bedrock.domain import (
    Invocation,
    InvocationStep,
    InvocationStepSummary,
    InvocationSummary,
    Session,
    SessionSummary,
    ImageSource,
    Image,
    ContentBlock,
    Payload,
)
from fondat.pagination import Cursor, Page

from ..clients import runtime_client
from ..decorators import operation
from ..pagination import decode_cursor, paginate
from ..cache import BedrockCache
from ..utils import convert_dict_keys_to_snake_case, parse_bedrock_datetime


@resource
class SessionsResource:
    """
    Resource for managing agent sessions.
    Provides access to create sessions and access specific ones.
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

    async def _list_sessions(
        self,
        max_results: int | None = None,
        cursor: Cursor | None = None,
    ) -> Page[SessionSummary]:
        """Internal method to list sessions without caching."""
        params = {}
        if max_results is not None:
            params["maxResults"] = max_results
        if cursor is not None:
            params["nextToken"] = decode_cursor(cursor)
        async with runtime_client(self.config_runtime) as client:
            with wrap_client_error():
                resp = await client.list_sessions(**params)
        return paginate(
            resp,
            items_key="sessionSummaries",
            mapper=lambda d: SessionSummary(
                memory_id=d.get("memoryId", ""),
                session_id=d["sessionId"],
                session_start_time=parse_bedrock_datetime(d["createdAt"]),
                session_expiry_time=parse_bedrock_datetime(
                    d.get("lastUpdatedAt", d["createdAt"])
                ),
                summary_text=d.get("description", ""),
                _factory=lambda sid=d["sessionId"], self=self: self[sid],
            ),
        )

    @operation(method="get", policies=lambda self: self.policies)
    async def get(
        self,
        *,
        max_results: int | None = None,
        cursor: Cursor | None = None,
    ) -> Page[SessionSummary]:
        """List agent sessions.

        Args:
            max_results: Maximum number of results to return
            cursor: Pagination cursor

        Returns:
            Page of session summaries
        """
        # Don't cache if pagination is being used
        if cursor is not None:
            return await self._list_sessions(max_results=max_results, cursor=cursor)

        # Use cache for first page results
        cache_key = f"agent_{self._agent_id}_sessions_{max_results}"
        return await self._cache.get_cached_page(
            cache_key=cache_key,
            page_type=Page[SessionSummary],
            fetch_func=self._list_sessions,
            max_results=max_results,
        )

    @operation(method="post", policies=lambda self: self.policies)
    async def create(
        self,
        *,
        encryptionKeyArn: str | None = None,
        sessionMetadata: dict[str, str] | None = None,
        tags: dict[str, str] | None = None,
    ) -> Session:
        """
        Create a new session.

        Args:
            encryptionKeyArn: Encryption key ARN
            sessionMetadata: Session metadata
            tags: Session tags

        Returns:
            Session details
        """
        params: dict[str, Any] = {}
        if encryptionKeyArn:
            params["encryptionKeyArn"] = encryptionKeyArn
        if sessionMetadata:
            params["sessionMetadata"] = sessionMetadata
        if tags:
            params["tags"] = tags
        async with runtime_client(self.config_runtime) as client:
            with wrap_client_error():
                response = await client.create_session(**params)
                session_data = {k: v for k, v in response.items() if k != "ResponseMetadata"}
                session_data.setdefault("lastUpdatedAt", session_data["createdAt"])
                # Convert camelCase to snake_case
                session_data = convert_dict_keys_to_snake_case(session_data)
                return Session(**session_data, _factory=lambda self=self: self)

    def __getitem__(self, session_id: str) -> "SessionResource":
        """Get a specific session resource.

        Args:
            session_id: Session identifier

        Returns:
            SessionResource instance
        """
        return SessionResource(
            self._agent_id,
            session_id,
            config_runtime=self.config_runtime,
            policies=self.policies,
        )


@resource
class SessionResource:
    """Resource for managing a specific session."""

    __slots__ = ("_agent_id", "_session_id", "config_runtime", "policies")

    def __init__(
        self,
        agent_id: str,
        session_id: str,
        *,
        config_runtime: Config | None = None,
        policies: Iterable[Policy] | None = None,
    ):
        self._agent_id = agent_id
        self._session_id = session_id
        self.config_runtime = config_runtime
        self.policies = policies

    @operation(method="get", policies=lambda self: self.policies)
    async def get(self) -> Session:
        """Get session details.

        Returns:
            Session details
        """
        async with runtime_client(self.config_runtime) as client:
            with wrap_client_error():
                response = await client.get_session(sessionIdentifier=self._session_id)
                session_data = {k: v for k, v in response.items() if k != "ResponseMetadata"}
                session_data.setdefault("lastUpdatedAt", session_data["createdAt"])
                # Convert camelCase to snake_case
                session_data = convert_dict_keys_to_snake_case(session_data)
                return Session(**session_data, _factory=lambda self=self: self)

    @operation(method="delete", policies=lambda self: self.policies)
    async def delete(self) -> None:
        """Delete session."""
        async with runtime_client(self.config_runtime) as client:
            with wrap_client_error():
                await client.delete_session(sessionIdentifier=self._session_id)

    @operation(method="post", policies=lambda self: self.policies)
    async def end(self) -> Session:
        """End session.

        Returns:
            Session end details
        """
        async with runtime_client(self.config_runtime) as client:
            with wrap_client_error():
                response = await client.end_session(sessionIdentifier=self._session_id)
                session_data = {k: v for k, v in response.items() if k != "ResponseMetadata"}
                # Convert camelCase to snake_case
                session_data = convert_dict_keys_to_snake_case(session_data)
                return Session(**session_data)

    @operation(method="patch", policies=lambda self: self.policies)
    async def update(
        self,
        *,
        sessionMetadata: dict[str, str] | None = None,
    ) -> Session:
        """Update session metadata.

        Args:
            sessionMetadata: Session metadata

        Returns:
            Updated session details
        """
        params = {"sessionIdentifier": self._session_id}
        if sessionMetadata is not None:
            params["sessionMetadata"] = sessionMetadata
        async with runtime_client(self.config_runtime) as client:
            with wrap_client_error():
                response = await client.update_session(**params)
                session_data = {k: v for k, v in response.items() if k != "ResponseMetadata"}
                # Convert camelCase to snake_case
                session_data = convert_dict_keys_to_snake_case(session_data)
                return Session(**session_data)

    @property
    def invocations(self) -> "InvocationsResource":
        """Get invocations resource."""
        return InvocationsResource(
            self._agent_id,
            self._session_id,
            config_runtime=self.config_runtime,
            policies=self.policies,
        )


@resource
class InvocationsResource:
    """Resource for managing session invocations."""

    __slots__ = ("_agent_id", "_session_id", "config_runtime", "policies", "_cache")

    def __init__(
        self,
        agent_id: str,
        session_id: str,
        *,
        config_runtime: Config | None = None,
        policies: Iterable[Policy] | None = None,
        cache_size: int = 100,
        cache_expire: int | float = 300,
    ):
        self._agent_id = agent_id
        self._session_id = session_id
        self.config_runtime = config_runtime
        self.policies = policies
        self._cache = BedrockCache(
            cache_size=cache_size,
            cache_expire=cache_expire,
        )

    async def _list_invocations(
        self,
        max_results: int | None = None,
        cursor: Cursor | None = None,
    ) -> Page[InvocationSummary]:
        """Internal method to list invocations without caching."""
        params = {
            "sessionIdentifier": self._session_id,
        }
        if max_results is not None:
            params["maxResults"] = max_results
        if cursor is not None:
            params["nextToken"] = decode_cursor(cursor)
        async with runtime_client(self.config_runtime) as client:
            with wrap_client_error():
                resp = await client.list_invocations(**params)
        return paginate(
            resp,
            items_key="invocationSummaries",
            mapper=lambda d: InvocationSummary(
                invocation_id=d["invocationId"],
                session_id=d["sessionId"],
                created_at=parse_bedrock_datetime(d["createdAt"]),
                status=d["status"],
                input_text=d["inputText"],
                _factory=lambda iid=d["invocationId"], self=self: self[iid],
            ),
        )

    @operation(method="get", policies=lambda self: self.policies)
    async def get(
        self,
        *,
        max_results: int | None = None,
        cursor: Cursor | None = None,
    ) -> Page[InvocationSummary]:
        """List session invocations.

        Args:
            max_results: Maximum number of results to return
            cursor: Pagination cursor

        Returns:
            Page of invocation summaries
        """
        # Don't cache if pagination is being used
        if cursor is not None:
            return await self._list_invocations(max_results=max_results, cursor=cursor)

        # Use cache for first page results
        cache_key = (
            f"agent_{self._agent_id}_session_{self._session_id}_invocations_{max_results}"
        )
        return await self._cache.get_cached_page(
            cache_key=cache_key,
            page_type=Page[InvocationSummary],
            fetch_func=self._list_invocations,
            max_results=max_results,
        )

    def __getitem__(self, invocation_id: str) -> "InvocationResource":
        """Get a specific invocation resource.

        Args:
            invocation_id: Invocation identifier

        Returns:
            InvocationResource instance
        """
        return InvocationResource(
            self._agent_id,
            self._session_id,
            invocation_id,
            config_runtime=self.config_runtime,
            policies=self.policies,
        )

    @operation(method="post", policies=lambda self: self.policies)
    async def create(self) -> Invocation:
        """Create a new invocation.

        Returns:
            Invocation details
        """
        async with runtime_client(self.config_runtime) as client:
            with wrap_client_error():
                response = await client.create_invocation(
                    sessionIdentifier=self._session_id,
                )
                invocation_data = {k: v for k, v in response.items() if k != "ResponseMetadata"}
                # Convert camelCase to snake_case
                invocation_data = convert_dict_keys_to_snake_case(invocation_data)
                # Ensure required fields are present
                invocation_data["session_id"] = self._session_id
                if "created_at" not in invocation_data:
                    invocation_data["created_at"] = datetime.now(timezone.utc)
                return Invocation(**invocation_data)


@resource
class InvocationResource:
    """Resource for managing a specific invocation."""

    __slots__ = ("_agent_id", "_session_id", "_invocation_id", "config_runtime", "policies")

    def __init__(
        self,
        agent_id: str,
        session_id: str,
        invocation_id: str,
        *,
        config_runtime: Config | None = None,
        policies: Iterable[Policy] | None = None,
    ):
        self._agent_id = agent_id
        self._session_id = session_id
        self._invocation_id = invocation_id
        self.config_runtime = config_runtime
        self.policies = policies

    @operation(method="post", policies=lambda self: self.policies)
    async def create(
        self,
        *,
        description: str | None = None,
    ) -> Invocation:
        """Create invocation.

        Args:
            description: Invocation description

        Returns:
            Invocation details
        """
        params = {
            "sessionIdentifier": self._session_id,
            "invocationId": self._invocation_id,
        }
        if description is not None:
            params["description"] = description
        async with runtime_client(self.config_runtime) as client:
            with wrap_client_error():
                response = await client.create_invocation(**params)
                return Invocation(**response)

    @operation(method="get", policies=lambda self: self.policies)
    async def get_steps(
        self,
        *,
        max_results: int | None = None,
        cursor: Cursor | None = None,
    ) -> Page[InvocationStepSummary]:
        """List invocation steps.

        Args:
            max_results: Maximum number of results to return
            cursor: Pagination cursor

        Returns:
            Page of step summaries
        """
        params = {
            "sessionIdentifier": self._session_id,
            "invocationIdentifier": self._invocation_id,
        }
        if max_results is not None:
            params["maxResults"] = max_results
        if cursor is not None:
            params["nextToken"] = decode_cursor(cursor)
        async with runtime_client(self.config_runtime) as client:
            with wrap_client_error():
                resp = await client.list_invocation_steps(**params)
        return paginate(
            resp,
            items_key="invocationStepSummaries",
            mapper=lambda d: InvocationStepSummary(
                invocation_id=d["invocationId"],
                invocation_step_id=d["invocationStepId"],
                invocation_step_time=parse_bedrock_datetime(d["invocationStepTime"]),
                _factory=lambda sid=d["invocationStepId"], self=self: self[sid],
            ),
        )

    @operation(method="post", policies=lambda self: self.policies)
    async def put_step(
        self,
        payload: dict[str, Any],
        invocation_step_time: datetime,
        *,
        invocation_step_id: str | None = None,
    ) -> str:
        """Add invocation step.

        Args:
            payload: Step payload
            invocation_step_time: Step timestamp
            invocation_step_id: Step identifier

        Returns:
            The invocation step ID
        """
        params = {
            "sessionIdentifier": self._session_id,
            "invocationIdentifier": self._invocation_id,
            "payload": payload,
            "invocationStepTime": invocation_step_time,
        }
        if invocation_step_id is not None:
            params["invocationStepId"] = invocation_step_id
        async with runtime_client(self.config_runtime) as client:
            with wrap_client_error():
                response = await client.put_invocation_step(**params)
                return response["invocationStepId"]

    def __getitem__(self, step_id: str) -> "StepResource":
        return StepResource(self, step_id)


class StepResource:
    def __init__(self, parent: "InvocationResource", step_id: str):
        self._parent = parent
        self._step_id = step_id
        self.config_runtime = parent.config_runtime
        self.policies = parent.policies

    @operation(method="get", policies=lambda self: self.policies)
    async def get(self) -> InvocationStep:
        async with runtime_client(self.config_runtime) as client:
            with wrap_client_error():
                response = await client.get_invocation_step(
                    sessionIdentifier=self._parent._session_id,
                    invocationIdentifier=self._parent._invocation_id,
                    invocationStepId=self._step_id,
                )
                step_data = response["invocationStep"]
                if "payload" in step_data:
                    payload_data = step_data["payload"]
                    content_blocks = []
                    for block in payload_data.get("contentBlocks", []):
                        image_data = None
                        if "image" in block:
                            image = block["image"]
                            source = ImageSource(**image["source"])
                            image_data = Image(format=image["format"], source=source)
                        content_blocks.append(
                            ContentBlock(image=image_data, text=block.get("text"))
                        )
                    step_data["payload"] = Payload(contentBlocks=content_blocks)
                mapped_data = {
                    "invocation_id": step_data["invocationId"],
                    "invocation_step_id": step_data["invocationStepId"],
                    "invocation_step_time": step_data["invocationStepTime"],
                    "payload": step_data["payload"],
                    "session_id": step_data["sessionId"],
                }
                return InvocationStep(**mapped_data)
