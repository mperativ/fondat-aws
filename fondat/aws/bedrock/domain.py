"""Domain classes for Bedrock entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, TypeVar, TYPE_CHECKING, Generic

if TYPE_CHECKING:
    from fondat.aws.bedrock.resources.agent import AgentResource
    from fondat.aws.bedrock.resources.flows import FlowResource
    from fondat.aws.bedrock.resources.prompts import PromptResource
    from fondat.aws.bedrock.resources.generic_resources import VersionResource, AliasResource
    from fondat.aws.bedrock.resources.sessions import SessionResource, InvocationResource
    from fondat.aws.bedrock.resources.action_groups import ActionGroupResource
    from fondat.aws.bedrock.resources.memory import MemorySessionResource
    from fondat.aws.bedrock.resources.collaborators import CollaboratorResource

T = TypeVar("T")


class _HasResource(Generic[T]):
    """Mixin to provide resource property functionality."""

    _factory: Optional[Callable[[], T]]

    @property
    def resource(self) -> T:
        """Get the full resource."""
        if self._factory is None:
            raise RuntimeError("Resource factory not provided")
        return self._factory()


@dataclass
class Agent:
    """Detailed information about a Bedrock agent."""

    agent_arn: str
    agent_id: str
    agent_name: str
    agent_status: str
    agent_collaboration: Optional[str] = None
    agent_resource_role_arn: Optional[str] = None
    agent_version: Optional[str] = None
    client_token: Optional[str] = None
    created_at: Optional[datetime] = None
    custom_orchestration: Optional[Dict[str, Any]] = None
    customer_encryption_key_arn: Optional[str] = None
    description: Optional[str] = None
    failure_reasons: Optional[List[str]] = field(default_factory=list)
    foundation_model: Optional[str] = None
    guardrail_configuration: Optional[Dict[str, Any]] = None
    idle_session_ttl_in_seconds: Optional[int] = None
    instruction: Optional[str] = None
    memory_configuration: Optional[Dict[str, Any]] = None
    orchestration_type: Optional[str] = None
    prepared_at: Optional[datetime] = None
    prompt_override_configuration: Optional[Dict[str, Any]] = None
    recommended_actions: Optional[List[str]] = field(default_factory=list)
    updated_at: Optional[datetime] = None


@dataclass
class AgentSummary(_HasResource["AgentResource"]):
    """Summary information about a Bedrock agent."""

    agent_id: str  # "agentId"
    agent_name: str  # "agentName"
    status: str  # "status"
    last_updated_at: Optional[datetime] = None  # "lastUpdatedAt"
    prepared_at: Optional[datetime] = None  # "preparedAt"
    _factory: Optional[Callable[[], "AgentResource"]] = field(
        default=None, repr=False, compare=False
    )


@dataclass
class AgentVersion:
    """Information about a specific version of a Bedrock agent."""

    agent_arn: str
    agent_id: str
    agent_name: str
    agent_status: str
    version: str
    created_at: datetime
    updated_at: datetime
    agent_collaboration: Optional[str] = None
    agent_resource_role_arn: Optional[str] = None
    customer_encryption_key_arn: Optional[str] = None
    description: Optional[str] = None
    failure_reasons: List[str] = field(default_factory=list)
    foundation_model: Optional[str] = None
    guardrail_configuration: Optional[Dict[str, Any]] = None
    idle_session_ttl_in_seconds: Optional[int] = None
    instruction: Optional[str] = None
    memory_configuration: Optional[Dict[str, Any]] = None
    prompt_override_configuration: Optional[Dict[str, Any]] = None
    recommended_actions: List[str] = field(default_factory=list)


@dataclass
class AgentAlias:
    """Information about an alias for a Bedrock agent."""

    agent_alias_arn: str
    agent_alias_id: str
    agent_alias_name: str
    agent_alias_status: str
    agent_id: str
    created_at: datetime
    updated_at: datetime
    agent_alias_history_events: Optional[List[Dict[str, Any]]] = field(default_factory=list)
    alias_invocation_state: Optional[str] = None
    client_token: Optional[str] = None
    description: Optional[str] = None
    failure_reasons: Optional[List[str]] = field(default_factory=list)
    routing_configuration: Optional[List[Dict[str, Any]]] = field(default_factory=list)


@dataclass
class AgentCollaborator:
    """Information about an agent collaborator."""

    agent_id: str
    agent_version: str
    collaborator_id: str
    collaborator_name: str
    created_at: datetime
    last_updated_at: datetime
    agent_descriptor: Dict[str, Any]
    client_token: Optional[str] = None
    collaboration_instruction: Optional[str] = None
    relay_conversation_history: Optional[str] = None


@dataclass
class AgentCollaboratorSummary(_HasResource["CollaboratorResource"]):
    """Summary information about an agent collaborator."""

    agent_id: str  # "agentId"
    collaborator_id: str  # "collaboratorId"
    collaborator_type: str  # "collaboratorType"
    created_at: datetime  # "createdAt"
    status: Optional[str] = None  # "status"
    invitation_id: Optional[str] = None  # "invitationId"
    _factory: Optional[Callable[[], "CollaboratorResource"]] = field(
        default=None, repr=False, compare=False
    )


@dataclass
class AgentInvocation:
    """Information about a Bedrock agent invocation."""

    session_id: str
    memory_id: Optional[str] = None
    content_type: Optional[str] = None
    completion: Optional[Any] = None  # EventStream type from AWS SDK


@dataclass
class Flow:
    """Information about a Bedrock flow."""

    arn: str
    flow_id: str
    flow_name: str
    status: str
    created_at: datetime
    updated_at: datetime
    definition: Dict[str, Any]
    version: str
    customer_encryption_key_arn: Optional[str] = None
    description: Optional[str] = None
    execution_role_arn: Optional[str] = None
    validations: Optional[List[Dict[str, Any]]] = field(default_factory=list)


@dataclass
class FlowSummary(_HasResource["FlowResource"]):
    """Summary information about a Bedrock flow."""

    flow_id: str  # "id"
    flow_name: str  # "name"
    status: str  # "status"
    created_at: datetime  # "createdAt"
    description: Optional[str] = None  # "description"
    _factory: Optional[Callable[[], "FlowResource"]] = field(
        default=None, repr=False, compare=False
    )


@dataclass
class FlowAlias:
    """Information about a Bedrock flow alias."""

    arn: str
    flow_alias_id: str
    flow_alias_name: str
    flow_id: str
    created_at: datetime
    updated_at: datetime
    concurrency_configuration: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    routing_configuration: Optional[List[Dict[str, Any]]] = field(default_factory=list)


@dataclass
class FlowInvocation:
    """Information about a Bedrock flow invocation."""

    execution_id: str
    response_stream: Optional[Any] = None  # EventStream type from AWS SDK


@dataclass
class Prompt:
    """Information about a Bedrock prompt."""

    arn: str
    prompt_id: str
    prompt_name: str
    version: str
    created_at: datetime
    updated_at: datetime
    variants: List[Dict[str, Any]]
    customer_encryption_key_arn: Optional[str] = None
    default_variant: Optional[str] = None
    description: Optional[str] = None


@dataclass
class PromptSummary(_HasResource["PromptResource"]):
    """Summary information about a Bedrock prompt."""

    prompt_id: str  # "promptId"
    prompt_name: str  # "promptName"
    created_at: datetime  # "createdAt"
    description: Optional[str] = None  # "description"
    _factory: Optional[Callable[[], "PromptResource"]] = field(
        default=None, repr=False, compare=False
    )


@dataclass
class Version:
    """Information about a Bedrock version."""

    arn: str
    version_id: str
    version: str
    status: str
    created_at: datetime
    updated_at: datetime
    customer_encryption_key_arn: Optional[str] = None
    description: Optional[str] = None
    execution_role_arn: Optional[str] = None
    definition: Optional[Dict[str, Any]] = None
    agent_arn: Optional[str] = None
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    agent_collaboration: Optional[str] = None
    agent_resource_role_arn: Optional[str] = None
    agent_status: Optional[str] = None
    failure_reasons: Optional[List[str]] = field(default_factory=list)
    foundation_model: Optional[str] = None
    guardrail_configuration: Optional[Dict[str, Any]] = None
    idle_session_ttl_in_seconds: Optional[int] = None
    instruction: Optional[str] = None
    memory_configuration: Optional[Dict[str, Any]] = None
    prompt_override_configuration: Optional[Dict[str, Any]] = None
    recommended_actions: Optional[List[str]] = field(default_factory=list)


@dataclass
class VersionSummary(_HasResource["VersionResource"]):
    """Summary information about a Bedrock version."""

    version_id: str  # "version"
    version_name: str  # "versionName"
    created_at: datetime  # "createdAt"
    description: Optional[str] = None  # "description"
    _factory: Optional[Callable[[], "VersionResource"]] = field(
        default=None, repr=False, compare=False
    )


@dataclass
class Alias:
    """Information about a Bedrock alias."""

    arn: str
    alias_id: str
    alias_name: str
    created_at: datetime
    updated_at: datetime
    routing_configuration: Optional[List[Dict[str, Any]]] = field(default_factory=list)
    description: Optional[str] = None
    # Agent alias specific fields
    agent_id: Optional[str] = None
    agent_alias_status: Optional[str] = None
    agent_alias_history_events: Optional[List[Dict[str, Any]]] = field(default_factory=list)
    alias_invocation_state: Optional[str] = None
    client_token: Optional[str] = None
    failure_reasons: Optional[List[str]] = field(default_factory=list)
    # Flow alias specific fields
    flow_id: Optional[str] = None
    concurrency_configuration: Optional[Dict[str, Any]] = None


@dataclass
class AliasSummary(_HasResource["AliasResource"]):
    """Summary information about a Bedrock alias."""

    alias_id: str  # "aliasId"
    alias_name: str  # "aliasName"
    created_at: datetime  # "createdAt"
    metadata: Optional[str] = None  # "metadata"
    _factory: Optional[Callable[[], "AliasResource"]] = field(
        default=None, repr=False, compare=False
    )


@dataclass
class Session:
    """Information about a Bedrock agent session."""

    session_id: str
    session_arn: str
    session_status: str
    created_at: datetime
    last_updated_at: datetime
    encryption_key_arn: Optional[str] = None
    session_metadata: Optional[Dict[str, str]] = field(default_factory=dict)


@dataclass
class SessionSummary(_HasResource["SessionResource"]):
    """Information about a session summary in memory."""

    memory_id: str
    session_id: str
    session_start_time: datetime
    session_expiry_time: datetime
    summary_text: str
    _factory: Optional[Callable[[], "SessionResource"]] = field(
        default=None, repr=False, compare=False
    )


@dataclass
class MemoryContents:
    """Information about memory contents."""

    memory_contents: Optional[List[Dict[str, SessionSummary]]] = field(default_factory=list)
    next_token: Optional[str] = None


@dataclass
class Invocation:
    """Information about a Bedrock agent invocation."""

    session_id: str
    session_arn: str
    session_status: str
    created_at: datetime
    last_updated_at: datetime
    encryption_key_arn: Optional[str] = None
    session_metadata: Optional[Dict[str, str]] = field(default_factory=dict)


@dataclass
class InvocationSummary(_HasResource["InvocationResource"]):
    """Summary information about a Bedrock agent invocation."""

    created_at: datetime  # "createdAt"
    invocation_id: str  # "invocationId"
    session_id: str  # "sessionId"
    status: str  # "status"
    input_text: Optional[str] = None  # "inputText"
    _factory: Optional[Callable[[], "InvocationResource"]] = field(
        default=None, repr=False, compare=False
    )


@dataclass
class InvocationStep:
    """Information about a step in a Bedrock agent invocation."""

    invocation_id: str
    invocation_step_id: str
    invocation_step_time: datetime
    session_id: str
    payload: Optional[Dict[str, Any]] = field(default_factory=dict)


@dataclass
class InvocationStepSummary:
    """Summary information about a step in a Bedrock agent invocation."""

    invocation_step_id: str  # "invocationStepId"
    session_id: str  # "sessionId"
    invocation_id: str  # "invocationId"
    status: str  # "status"
    created_at: datetime  # "createdAt"
    ended_at: Optional[datetime] = None  # "endedAt"
    payload: Optional[Dict[str, Any]] = field(default_factory=dict)  # "payload"


@dataclass
class ActionGroup:
    """Information about an action group for a Bedrock agent."""

    action_group_id: str
    action_group_name: str
    action_group_state: str
    agent_id: str
    agent_version: str
    created_at: datetime
    updated_at: datetime
    action_group_executor: Optional[Dict[str, Any]] = None
    api_schema: Optional[Dict[str, Any]] = None
    client_token: Optional[str] = None
    description: Optional[str] = None
    function_schema: Optional[Dict[str, Any]] = None
    parent_action_group_signature_params: Optional[Dict[str, str]] = field(default_factory=dict)
    parent_action_signature: Optional[str] = None


@dataclass
class ActionGroupSummary(_HasResource["ActionGroupResource"]):
    """Summary information about an action group for a Bedrock agent."""

    action_group_id: str  # "actionGroupId"
    action_group_name: str  # "actionGroupName"
    description: Optional[str] = None  # "description"
    schema_arn: Optional[str] = None  # "schemaArn"
    executor_arn: Optional[str] = None  # "executorArn"
    _factory: Optional[Callable[[], "ActionGroupResource"]] = field(
        default=None, repr=False, compare=False
    )


@dataclass
class MemorySession:
    """Information about a Bedrock memory session."""

    memory_id: str  # "memoryId"
    memory_arn: str  # "memoryArn"
    memory_name: str  # "memoryName"
    created_at: datetime  # "createdAt"
    updated_at: Optional[datetime] = None  # "updatedAt"
    description: Optional[str] = None  # "description"
    metadata: Optional[Dict[str, Any]] = None  # "metadata"


@dataclass
class MemorySessionSummary(_HasResource["MemorySessionResource"]):
    """Summary information about a Bedrock memory session."""

    memory_id: str  # "memoryId"
    memory_name: str  # "memoryName"
    created_at: datetime  # "createdAt"
    updated_at: Optional[datetime] = None  # "updatedAt"
    description: Optional[str] = None  # "description"
    _factory: Optional[Callable[[], "MemorySessionResource"]] = field(
        default=None, repr=False, compare=False
    )
