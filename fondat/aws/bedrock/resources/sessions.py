"""Resource for managing agent sessions."""

from collections.abc import Iterable
from typing import Any, Mapping
from datetime import datetime

from fondat.aws.client import Config
from fondat.resource import resource
from fondat.security import Policy

from ..clients import runtime_client
from ..decorators import operation
from ..pagination import paginate


@resource
class SessionsResource:
    """
    Resource for managing agent sessions.
    Provides access to create, retrieve, update, and delete sessions.
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

    @operation(method="post", policies=lambda self: self.policies)
    async def create(
        self,
        *,
        encryptionKeyArn: str | None = None,
        sessionMetadata: dict[str, str] | None = None,
        tags: dict[str, str] | None = None,
    ) -> Mapping[str, Any]:
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
            return await client.create_session(**params)

    @operation(method="get", policies=lambda self: self.policies)
    async def get(self, sessionIdentifier: str) -> Mapping[str, Any]:
        """
        Retrieve details of a specific session.

        Args:
            sessionIdentifier: Session identifier

        Returns:
            Session details
        """
        async with runtime_client(self.config_runtime) as client:
            return await client.get_session(sessionIdentifier=sessionIdentifier)

    @operation(method="delete", policies=lambda self: self.policies)
    async def delete(self, sessionIdentifier: str) -> None:
        """Delete session.

        Args:
            sessionIdentifier: Session identifier
        """
        async with runtime_client(self.config_runtime) as client:
            await client.delete_session(sessionIdentifier=sessionIdentifier)

    @operation(method="post", policies=lambda self: self.policies)
    async def end(self, sessionIdentifier: str) -> Mapping[str, Any]:
        """End session.

        Args:
            sessionIdentifier: Session identifier

        Returns:
            Session end details
        """
        async with runtime_client(self.config_runtime) as client:
            return await client.end_session(sessionIdentifier=sessionIdentifier)

    @operation(method="patch", policies=lambda self: self.policies)
    async def update(
        self,
        sessionIdentifier: str,
        *,
        sessionMetadata: dict[str, str] | None = None,
    ) -> Mapping[str, Any]:
        """Update session metadata.

        Args:
            sessionIdentifier: Session identifier
            sessionMetadata: Session metadata

        Returns:
            Updated session details
        """
        params = {"sessionIdentifier": sessionIdentifier}
        if sessionMetadata is not None:
            params["sessionMetadata"] = sessionMetadata
        async with runtime_client(self.config_runtime) as client:
            return await client.update_session(**params)

    @property
    def invocations(self) -> "InvocationsResource":
        """Get invocations resource."""
        return InvocationsResource(
            self._agent_id, config_runtime=self.config_runtime, policies=self.policies
        )


@resource
class InvocationsResource:
    """Resource for managing session invocations."""

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

    @operation(method="post", policies=lambda self: self.policies)
    async def create(
        self,
        sessionIdentifier: str,
        invocationId: str,
        *,
        description: str | None = None,
    ) -> Mapping[str, Any]:
        """Create invocation.

        Args:
            sessionIdentifier: Session identifier
            invocationId: Invocation identifier
            description: Invocation description

        Returns:
            Invocation details
        """
        params = {
            "sessionIdentifier": sessionIdentifier,
            "invocationId": invocationId,
        }
        if description is not None:
            params["description"] = description
        async with runtime_client(self.config_runtime) as client:
            return await client.create_invocation(**params)

    @operation(method="post", policies=lambda self: self.policies)
    async def put_step(
        self,
        sessionIdentifier: str,
        invocationIdentifier: str,
        payload: dict[str, Any],
        invocationStepTime: datetime,
        *,
        invocationStepId: str | None = None,
    ) -> Mapping[str, Any]:
        """Add invocation step.

        Args:
            sessionIdentifier: Session identifier
            invocationIdentifier: Invocation identifier
            payload: Step payload
            invocationStepTime: Step timestamp
            invocationStepId: Step identifier

        Returns:
            Step details
        """
        params = {
            "sessionIdentifier": sessionIdentifier,
            "invocationIdentifier": invocationIdentifier,
            "payload": payload,
            "invocationStepTime": invocationStepTime,
        }
        if invocationStepId is not None:
            params["invocationStepId"] = invocationStepId
        async with runtime_client(self.config_runtime) as client:
            return await client.put_invocation_step(**params)

    @operation(method="get", policies=lambda self: self.policies)
    async def get_step(
        self,
        sessionIdentifier: str,
        invocationIdentifier: str,
        invocationStepId: str,
    ) -> Mapping[str, Any]:
        """Get invocation step details.

        Args:
            sessionIdentifier: Session identifier
            invocationIdentifier: Invocation identifier
            invocationStepId: Step identifier

        Returns:
            Step details
        """
        async with runtime_client(self.config_runtime) as client:
            return await client.get_invocation_step(
                sessionIdentifier=sessionIdentifier,
                invocationIdentifier=invocationIdentifier,
                invocationStepId=invocationStepId,
            )

    @operation(method="get", policies=lambda self: self.policies)
    async def list_steps(
        self,
        sessionIdentifier: str,
        invocationIdentifier: str | None = None,
        *,
        max_results: int | None = None,
        cursor: str | None = None,
    ) -> Any:
        """List invocation steps.

        Args:
            sessionIdentifier: Session identifier
            invocationIdentifier: Invocation identifier
            max_results: Maximum number of results to return
            cursor: Pagination cursor

        Returns:
            Page of step summaries
        """
        params = {"sessionIdentifier": sessionIdentifier}
        if invocationIdentifier is not None:
            params["invocationIdentifier"] = invocationIdentifier
        if max_results is not None:
            params["maxResults"] = max_results
        if cursor is not None:
            params["nextToken"] = cursor
        async with runtime_client(self.config_runtime) as client:
            resp = await client.list_invocation_steps(**params)
        return paginate(resp, items_key="invocationStepSummaries")

    @operation(method="get", policies=lambda self: self.policies)
    async def list(
        self,
        sessionIdentifier: str,
        *,
        max_results: int | None = None,
        cursor: str | None = None,
    ) -> Any:
        """List session invocations.

        Args:
            sessionIdentifier: Session identifier
            max_results: Maximum number of results to return
            cursor: Pagination cursor

        Returns:
            Page of invocation summaries
        """
        params = {"sessionIdentifier": sessionIdentifier}
        if max_results is not None:
            params["maxResults"] = max_results
        if cursor is not None:
            params["nextToken"] = cursor
        async with runtime_client(self.config_runtime) as client:
            resp = await client.list_invocations(**params)
        return paginate(resp, items_key="invocationSummaries")
