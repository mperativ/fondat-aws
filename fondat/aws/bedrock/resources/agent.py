"""Resource for managing a specific Bedrock agent."""

from collections.abc import Iterable
from typing import Any, Mapping

from fondat.aws.client import Config, wrap_client_error
from fondat.resource import resource
from fondat.security import Policy

from ..clients import agent_client, runtime_client
from ..decorators import operation

from .versions import VersionsResource
from .aliases import AliasesResource
from .action_groups import ActionGroupsResource
from .collaborators import CollaboratorsResource
from .prompts import PromptsResource
from .flows import FlowsResource
from .sessions import SessionsResource
from .memory import MemoryResource


@resource
class AgentResource:
    """
    Resource for managing a specific Bedrock agent.
    Provides access to agent metadata, versions, aliases, action groups, and runtime operations.
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
    async def get(self) -> Mapping[str, Any]:
        """
        Retrieve detailed information about the agent.

        Returns:
            Mapping containing agent details
        """
        async with agent_client(self.config_agent) as client:
            with wrap_client_error():
                return await client.get_agent(agentId=self._id)

    @operation(method="post", policies=lambda self: self.policies)
    async def prepare(self) -> Mapping[str, Any]:
        """
        Prepare the agent for use.

        Returns:
            Mapping containing preparation details
        """
        async with agent_client(self.config_agent) as client:
            with wrap_client_error():
                return await client.prepare_agent(agentId=self._id)

    @operation(method="post", policies=lambda self: self.policies)
    async def invoke(
        self,
        inputText: str,
        sessionId: str,
        agentAliasId: str,
        *,
        enableTrace: bool = False,
        endSession: bool = False,
        bedrockModelConfigurations: dict | None = None,
        memoryId: str | None = None,
        sessionState: dict | None = None,
        sourceArn: str | None = None,
        streamingConfigurations: dict | None = None,
    ) -> Mapping[str, Any]:
        """
        Invoke the agent with the given input.

        Args:
            inputText: Input text to process
            sessionId: Session identifier
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

    @operation(method="post", policies=lambda self: self.policies)
    async def invoke_inline_agent(
        self,
        *,
        foundationModel: str,
        instruction: str,
        sessionId: str,
        inputText: str,
        actionGroups: list[dict] | None = None,
        agentCollaboration: str | None = None,
        agentName: str | None = None,
        bedrockModelConfigurations: dict | None = None,
        collaboratorConfigurations: list[dict] | None = None,
        collaborators: list[dict] | None = None,
        customOrchestration: dict | None = None,
        customerEncryptionKeyArn: str | None = None,
        enableTrace: bool = False,
        endSession: bool = False,
        guardrailConfiguration: dict | None = None,
        idleSessionTTLInSeconds: int | None = None,
        inlineSessionState: dict | None = None,
        knowledgeBases: list[dict] | None = None,
        orchestrationType: str | None = None,
        promptOverrideConfiguration: dict | None = None,
        streamingConfigurations: dict | None = None,
    ) -> Mapping[str, Any]:
        """
        Invoke an inline Amazon Bedrock agent.

        Required:
        foundationModel: the underlying model to orchestrate
        instruction: what the agent should do  
        sessionId:   unique session identifier  
        inputText:   user input to send to the agent

        Optional: you can pass any of the other inline-agent config blocks below.
        """
        params: dict[str, Any] = {
            "agentId": self._id,
            "foundationModel": foundationModel,
            "instruction": instruction,
            "sessionId": sessionId,
            "inputText": inputText,
        }
        if actionGroups:
            params["actionGroups"] = actionGroups
        if agentCollaboration:
            params["agentCollaboration"] = agentCollaboration
        if agentName:
            params["agentName"] = agentName
        if bedrockModelConfigurations:
            params["bedrockModelConfigurations"] = bedrockModelConfigurations
        if collaboratorConfigurations:
            params["collaboratorConfigurations"] = collaboratorConfigurations
        if collaborators:
            params["collaborators"] = collaborators
        if customOrchestration:
            params["customOrchestration"] = customOrchestration
        if customerEncryptionKeyArn:
            params["customerEncryptionKeyArn"] = customerEncryptionKeyArn
        if enableTrace:
            params["enableTrace"] = True
        if endSession:
            params["endSession"] = True
        if guardrailConfiguration:
            params["guardrailConfiguration"] = guardrailConfiguration
        if idleSessionTTLInSeconds is not None:
            params["idleSessionTTLInSeconds"] = idleSessionTTLInSeconds
        if inlineSessionState:
            params["inlineSessionState"] = inlineSessionState
        if knowledgeBases:
            params["knowledgeBases"] = knowledgeBases
        if orchestrationType:
            params["orchestrationType"] = orchestrationType
        if promptOverrideConfiguration:
            params["promptOverrideConfiguration"] = promptOverrideConfiguration
        if streamingConfigurations:
            params["streamingConfigurations"] = streamingConfigurations

        async with runtime_client(self.config_runtime) as client:
            with wrap_client_error():
                return await client.invoke_inline_agent(**params)

    @property
    def versions(self) -> VersionsResource:
        """Get the versions resource for this agent."""
        return VersionsResource(
            self._id, config_agent=self.config_agent, policies=self.policies
        )

    @property
    def aliases(self) -> AliasesResource:
        """Get the aliases resource for this agent."""
        return AliasesResource(self._id, config_agent=self.config_agent, policies=self.policies)

    @property
    def action_groups(self) -> ActionGroupsResource:
        """Get the action groups resource for this agent."""
        return ActionGroupsResource(
            self._id, config_agent=self.config_agent, policies=self.policies
        )

    @property
    def flows(self) -> FlowsResource:
        """Get the flows resource for this agent."""
        return FlowsResource(
            self._id,
            config_agent=self.config_agent,
            config_runtime=self.config_runtime,
            policies=self.policies,
        )

    @property
    def sessions(self) -> SessionsResource:
        """Get the sessions resource for this agent."""
        return SessionsResource(
            self._id,
            config_runtime=self.config_runtime,
            policies=self.policies,
        )

    @property
    def memory(self) -> MemoryResource:
        """Get the memory resource for this agent."""
        return MemoryResource(
            self._id,
            config_runtime=self.config_runtime,
            policies=self.policies,
        )

    @property
    def prompts(self) -> PromptsResource:
        """Get the prompts resource for this agent."""
        return PromptsResource(
            self._id,
            config_agent=self.config_agent,
            policies=self.policies,
        )

    @property
    def collaborators(self) -> CollaboratorsResource:
        """Get the collaborators resource for this agent."""
        return CollaboratorsResource(
            self._id,
            config_agent=self.config_agent,
            policies=self.policies,
        )
