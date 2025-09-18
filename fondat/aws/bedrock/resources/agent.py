"""Resource for managing a specific Bedrock agent."""

from collections.abc import Iterable

from fondat.aws.bedrock.domain import Agent, AgentInvocation, Invocation
from fondat.aws.bedrock.resources.aliases import AliasesResource
from fondat.aws.client import Config, wrap_client_error
from fondat.resource import resource
from fondat.security import Policy
from fondat.aws.bedrock.utils import convert_dict_keys_to_snake_case
from contextlib import AsyncExitStack

from ..clients import agent_client, runtime_client
from ..decorators import operation

from .versions import VersionsResource
from .generic_resources import GenericAliasResource
from .action_groups import ActionGroupsResource
from .collaborators import CollaboratorsResource
from .flows import FlowsResource
from .sessions import SessionsResource
from .memory import MemoryResource
from .streams import AgentStream


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

    def _process_agent_response(self, response: dict) -> dict:
        """Process agent response from client.
        """
        data = {k: v for k, v in response.items() if k != "ResponseMetadata"}
        if "agent" not in data:
            raise ValueError("Missing 'agent' in response")
        data.update(data.pop("agent"))
        
        required_fields = ["agentId", "agentName", "agentStatus"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field '{field}' in agent data")
        
        data["_factory"] = lambda: self
        return convert_dict_keys_to_snake_case(data)

    @operation(method="get", policies=lambda self: self.policies)
    async def get(self) -> Agent:
        """
        Retrieve detailed information about the agent.

        Returns:
            Agent: Detailed information about the Bedrock agent
        """
        async with agent_client(self.config_agent) as client:
            with wrap_client_error():
                response = await client.get_agent(agentId=self._id)
                data = self._process_agent_response(response)
                return Agent(**data)

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
    ) -> AgentInvocation:
        """
        Invoke the agent with the given input.

        Args:
            inputText: Input text to process
            sessionId: Session identifier. If None, a new session will be created automatically
            agentAliasId: Agent alias identifier
            enableTrace: Enable trace information
            endSession: End session after invocation
            bedrockModelConfigurations: Model configurations
            memoryId: Memory identifier
            sessionState: Session state
            sourceArn: Source ARN
            streamingConfigurations: Streaming configurations

        Returns:
            AgentInvocation: Information about the agent invocation. Note that even when a new session
            is created (sessionId=None), this method returns an AgentInvocation, not a Session.
        """
        if sessionId is None:
            session = await self.sessions.create()
            sessionId = session["sessionId"]

        params = {
            "agentId": self._id,
            "inputText": inputText,
            "sessionId": sessionId,
            "agentAliasId": agentAliasId,
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
                response = await client.invoke_agent(**params)
                data = {k: v for k, v in response.items() if k != "ResponseMetadata"}
                data = convert_dict_keys_to_snake_case(data)
                data["_factory"] = lambda: self
                return AgentInvocation(**data)

    @operation(method="post", type="mutation", policies=lambda self: self.policies)
    async def invoke_streaming(
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
    ) -> AgentStream:
        """
        Invoke the agent with streaming response.

        Args:
            inputText: Input text to process
            sessionId: Session identifier. If None, a new session will be created automatically
            agentAliasId: Agent alias identifier
            enableTrace: Enable trace information
            endSession: End session after invocation
            bedrockModelConfigurations: Model configurations
            memoryId: Memory identifier
            sessionState: Session state
            sourceArn: Source ARN
            streamingConfigurations: Streaming configurations

        Returns:
            AgentStream: An async iterator of completion events
        """
        if sessionId is None:
            session = await self.sessions.create()
            sessionId = session["sessionId"]

        params = {
            "agentId": self._id,
            "inputText": inputText,
            "sessionId": sessionId,
            "agentAliasId": agentAliasId,
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

        stack = AsyncExitStack()
        client = await stack.enter_async_context(runtime_client(self.config_runtime))
        with wrap_client_error():
            response = await client.invoke_agent(**params)

        # AgentStream will call stack.aclose() when iteration finishes
        return AgentStream(response, stack)

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
