"""Resource for managing a specific Bedrock agent."""

from collections.abc import Iterable

from fondat.aws.bedrock.domain import Agent, Invocation
from fondat.aws.bedrock.resources.aliases import AliasesResource
from fondat.aws.client import Config, wrap_client_error
from fondat.resource import resource
from fondat.security import Policy

from ..clients import agent_client, runtime_client
from ..decorators import operation

from .versions import VersionsResource
from .generic_resources import GenericAliasResource
from .action_groups import ActionGroupsResource
from .collaborators import CollaboratorsResource
from .flows import FlowsResource
from .sessions import SessionsResource
from .memory import MemoryResource


@resource
class AgentResource:
    """
    Resource for managing a specific Bedrock agent.
    Now delegates versions and aliases to functions that return generic instances.
    """

    __slots__ = ("_id", "config_agent", "config_runtime", "policies")

    def __init__(
        self,
        agent_id: str,
        *,
        config_agent: Config | None = None,
        config_runtime: Config | None = None,
        policies: Iterable[Policy] | None = None,
    ):
        self._id = agent_id
        self.config_agent = config_agent
        self.config_runtime = config_runtime
        self.policies = policies

    @operation(method="get", policies=lambda self: self.policies)
    async def get(self) -> Agent:
        """
        Retrieve detailed information about the agent.

        Returns:
            Mapping containing agent details
        """
        async with agent_client(self.config_agent) as client:
            with wrap_client_error():
                return await client.get_agent(agentId=self._id)


    @operation(method="post", policies=lambda self: self.policies)
    async def invoke(
        self,
        inputText: str,
        sessionId: str | None,
        agentAliasId: str,
        *,
        enableTrace: bool = False,
        endSession: bool = False,
        bedrockModelConfigurations: dict | None = None,
        memoryId: str | None = None,
        sessionState: dict | None = None,
        sourceArn: str | None = None,
        streamingConfigurations: dict | None = None,
    ) -> Invocation:
        """
        Invoke the agent with the given input.

        Args:
            inputText: Input text to process
            sessionId: Session identifier. If None, a new session will be created
            agentAliasId: Agent alias identifier
            enableTrace: Enable trace information
            endSession: End session after invocation
            bedrockModelConfigurations: Model configurations
            memoryId: Memory identifier
            sessionState: Session state
            sourceArn: Source ARN
            streamingConfigurations: Streaming configurations

        Returns:
            Mapping containing agent invocation results
        """
        if sessionId is None:
            session = await self.sessions.create()
            sessionId = session["sessionId"]

        params = {
            "agentId": self._id,
            "inputText": inputText,
            "sessionId": sessionId,
            "agentAliasId": agentAliasId
        }
        if enableTrace:
            params["enableTrace"] = True
        if endSession:
            params["endSession"] = True
        if bedrockModelConfigurations:
            params["bedrockModelConfigurations"] = bedrockModelConfigurations
        if memoryId:
            params["memoryId"] = memoryId
        if sessionState:
            params["sessionState"] = sessionState
        if sourceArn:
            params["sourceArn"] = sourceArn
        if streamingConfigurations:
            params["streamingConfigurations"] = streamingConfigurations
        async with runtime_client(self.config_runtime) as client:
            with wrap_client_error():
                return await client.invoke_agent(**params)

    @property
    def versions(self):
        """
        Property that returns the agent versions.
        """
        return VersionsResource(
            self._id,
            config_agent=self.config_agent,
            policies=self.policies,
            cache_size=100,
            cache_expire=300,
        )

    @property
    def aliases(self) -> GenericAliasResource:
        """
        Property that returns the agent aliases.
        """
        return AliasesResource(
            self._id,
            config_agent=self.config_agent,
            policies=self.policies,
            cache_size=100,
            cache_expire=300,
        )

    @property
    def action_groups(self) -> ActionGroupsResource:
        """Get the action groups resource for this agent."""
        return ActionGroupsResource(
            self._id,
            config_agent=self.config_agent,
            policies=self.policies,
            cache_size=100,
            cache_expire=300,
        )

    @property
    def flows(self) -> FlowsResource:
        """Get the flows resource for this agent."""
        return FlowsResource(
            self._id,
            config_agent=self.config_agent,
            config_runtime=self.config_runtime,
            policies=self.policies,
            cache_size=100,
            cache_expire=300,
        )

    @property
    def sessions(self) -> SessionsResource:
        """Get the sessions resource for this agent."""
        return SessionsResource(
            self._id,
            config_runtime=self.config_runtime,
            policies=self.policies,
            cache_size=100,
            cache_expire=300,
        )

    @property
    def memory(self) -> MemoryResource:
        """Get the memory resource for this agent."""
        return MemoryResource(
            self._id,
            config_runtime=self.config_runtime,
            policies=self.policies,
            cache_size=100,
            cache_expire=300,
        )

    @property
    def collaborators(self) -> CollaboratorsResource:
        """Get the collaborators resource for this agent."""
        return CollaboratorsResource(
            self._id,
            config_agent=self.config_agent,
            policies=self.policies,
            cache_size=100,
            cache_expire=300,
        )
