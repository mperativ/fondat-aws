"""Domain classes for Bedrock entities.

This module contains pure dataclasses that model the **domain** objects returned by the
Fondat‑AWS Bedrock SDK.  They are organised in thematic sections so that related types
are easy to locate:

1.  **Core helpers**   – mixins and generics used by the rest of the file.
2.  **Agent domain**   – agent, versions, aliases, collaborators, etc.
3.  **Flow domain**    – flows, versions, aliases, invocations.
4.  **Prompt domain**  – prompts and their versions.
5.  **Session / Memory** – sessions, memory contents.
6.  **Invocation**     – agent invocation payloads & steps.
7.  **Action Groups**  – action‑group specific structures.
8.  **Rich content**   – images, content blocks, payloads.

Each *_Summary* dataclass inherits from ``_HasResource`` so that the full resource can be
lazily fetched with the :pyattr:`resource` property.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Literal,
    Optional,
    TypeVar,
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    from fondat.aws.bedrock.resources.action_groups import ActionGroupResource
    from fondat.aws.bedrock.resources.agent import AgentResource
    from fondat.aws.bedrock.resources.collaborators import CollaboratorResource
    from fondat.aws.bedrock.resources.flows import FlowResource
    from fondat.aws.bedrock.resources.generic_resources import AliasResource, VersionResource
    from fondat.aws.bedrock.resources.memory import MemorySessionResource
    from fondat.aws.bedrock.resources.prompts import PromptResource
    from fondat.aws.bedrock.resources.sessions import InvocationResource, SessionResource

T = TypeVar("T")

# ===========================================================================
# 1.  Core helpers
# ===========================================================================


class _HasResource(Generic[T]):
    """Mixin that lazily resolves the Fondat *resource* representing the full object."""

    _factory: Optional[Callable[[], T]]

    @property
    def resource(self) -> T:  # noqa: D401 – property docstring style
        """Return the live Fondat resource."""
        if self._factory is None:  # safety‑net – should not happen in normal flow
            raise RuntimeError("Resource factory not provided")
        return self._factory()


# ===========================================================================
# 2.  Agent domain
# ===========================================================================


@dataclass
class Agent:  # noqa: D101 – external API fields retain AWS camelCase
    """Full detail of a Bedrock **Agent**."""

    agentId: str
    agentArn: Optional[str] = None
    agentName: Optional[str] = None
    agentStatus: Optional[str] = None
    agentCollaboration: Optional[str] = None
    agentResourceRoleArn: Optional[str] = None
    agentVersion: Optional[str] = None
    clientToken: Optional[str] = None
    createdAt: Optional[datetime] = None
    customOrchestration: Optional[Dict[str, Any]] = None
    customerEncryptionKeyArn: Optional[str] = None
    description: Optional[str] = None
    failureReasons: List[str] = field(default_factory=list)
    foundationModel: Optional[str] = None
    guardrailConfiguration: Optional[Dict[str, Any]] = None
    idleSessionTTLInSeconds: Optional[int] = None
    instruction: Optional[str] = None
    memoryConfiguration: Optional[Dict[str, Any]] = None
    orchestrationType: Optional[str] = None
    preparedAt: Optional[datetime] = None
    promptOverrideConfiguration: Optional[Dict[str, Any]] = None
    recommendedActions: List[str] = field(default_factory=list)
    updatedAt: Optional[datetime] = None


@dataclass
class AgentSummary(_HasResource["AgentResource"]):
    """Lightweight view returned by *ListAgents*."""

    agent_id: str
    agent_name: str
    status: str
    last_updated_at: Optional[datetime] = None
    prepared_at: Optional[datetime] = None
    _factory: Optional[Callable[[], "AgentResource"]] = field(default=None, repr=False, compare=False)


# -- Agent Versions ---------------------------------------------------------


@dataclass
class AgentVersion:  # noqa: D101
    versionArn: str
    versionId: str
    version: str
    status: str
    createdAt: datetime
    updatedAt: datetime
    agentId: str
    agentName: str
    agentStatus: str
    agentVersion: str
    # optional extras
    agentCollaboration: Optional[str] = None
    agentResourceRoleArn: Optional[str] = None
    customerEncryptionKeyArn: Optional[str] = None
    description: Optional[str] = None
    failureReasons: List[str] = field(default_factory=list)
    foundationModel: Optional[str] = None
    guardrailConfiguration: Optional[Dict[str, Any]] = None
    idleSessionTtlInSeconds: Optional[int] = None
    instruction: Optional[str] = None
    memoryConfiguration: Optional[Dict[str, Any]] = None
    promptOverrideConfiguration: Optional[Dict[str, Any]] = None
    recommendedActions: List[str] = field(default_factory=list)
    executionRoleArn: Optional[str] = None
    versionName: Optional[str] = None
    definition: Optional[Dict[str, Any]] = None


# -- Agent Aliases ----------------------------------------------------------


@dataclass
class AgentAlias:  # noqa: D101
    agent_alias_arn: str
    agent_alias_id: str
    agent_alias_name: str
    agent_alias_status: str
    agent_id: str
    created_at: datetime
    updated_at: datetime
    agent_alias_history_events: List[Dict[str, Any]] = field(default_factory=list)
    alias_invocation_state: Optional[str] = None
    client_token: Optional[str] = None
    description: Optional[str] = None
    failure_reasons: List[str] = field(default_factory=list)
    routing_configuration: List[Dict[str, Any]] = field(default_factory=list)


# -- Agent Collaborators ----------------------------------------------------


@dataclass
class AgentCollaborator:  # noqa: D101
    agentId: str
    agentVersion: str
    collaboratorId: str
    collaboratorName: str
    createdAt: datetime
    lastUpdatedAt: datetime
    agentDescriptor: Dict[str, Any]
    clientToken: Optional[str] = None
    collaborationInstruction: Optional[str] = None
    relayConversationHistory: Optional[str] = None


@dataclass
class AgentCollaboratorSummary(_HasResource["CollaboratorResource"]):
    agent_id: str
    collaborator_id: str
    collaborator_type: str
    created_at: datetime
    status: Optional[str] = None
    invitation_id: Optional[str] = None
    _factory: Optional[Callable[[], "CollaboratorResource"]] = field(default=None, repr=False, compare=False)


# -- Agent Invocation -------------------------------------------------------


@dataclass
class AgentInvocation:  # noqa: D101
    completion: Any  # EventStream from AWS SDK
    contentType: Optional[str] = None
    memoryId: Optional[str] = None
    sessionId: Optional[str] = None


# ===========================================================================
# 3.  Flow domain
# ===========================================================================


@dataclass
class Flow:  # noqa: D101
    flowArn: str
    flowId: str
    flowName: str
    status: str
    createdAt: datetime
    updatedAt: datetime
    definition: Dict[str, Any]
    version: str
    customerEncryptionKeyArn: Optional[str] = None
    description: Optional[str] = None
    executionRoleArn: Optional[str] = None
    validations: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class FlowSummary(_HasResource["FlowResource"]):
    flow_id: str
    flow_name: str
    status: str
    created_at: datetime
    description: Optional[str] = None
    _factory: Optional[Callable[[], "FlowResource"]] = field(default=None, repr=False, compare=False)


# -- Flow Versions & Aliases ------------------------------------------------


@dataclass
class FlowVersion:  # noqa: D101
    versionArn: str
    versionId: str
    version: str
    status: str
    createdAt: datetime
    updatedAt: datetime
    flowId: str
    flowName: str
    flowVersion: str
    definition: Dict[str, Any]
    customerEncryptionKeyArn: Optional[str] = None
    description: Optional[str] = None
    executionRoleArn: Optional[str] = None
    validations: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class FlowAlias:  # noqa: D101
    arn: str
    flow_alias_id: str
    flow_alias_name: str
    flow_id: str
    created_at: datetime
    updated_at: datetime
    concurrency_configuration: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    routing_configuration: List[Dict[str, Any]] = field(default_factory=list)


# -- Flow Invocation --------------------------------------------------------


@dataclass
class FlowInvocation:  # noqa: D101
    executionId: str
    responseStream: Optional[Any] = None  # EventStream


# ===========================================================================
# 4.  Prompt domain
# ===========================================================================


@dataclass
class Prompt:  # noqa: D101
    promptArn: str
    promptId: str
    promptName: str
    version: str
    createdAt: datetime
    updatedAt: datetime
    variants: List[Dict[str, Any]]
    customerEncryptionKeyArn: Optional[str] = None
    defaultVariant: Optional[str] = None
    description: Optional[str] = None


@dataclass
class PromptSummary(_HasResource["PromptResource"]):
    prompt_id: str
    prompt_name: str
    created_at: datetime
    description: Optional[str] = None
    _factory: Optional[Callable[[], "PromptResource"]] = field(default=None, repr=False, compare=False)


@dataclass
class PromptVersion:  # noqa: D101
    versionArn: str
    versionId: str
    version: str
    status: str
    createdAt: datetime
    updatedAt: datetime
    promptId: str
    promptName: str
    promptVersion: str
    variants: List[Dict[str, Any]]
    customerEncryptionKeyArn: Optional[str] = None
    defaultVariant: Optional[str] = None
    description: Optional[str] = None


# ===========================================================================
# 5.  Session & Memory domain
# ===========================================================================


@dataclass
class Session:  # noqa: D101
    sessionId: str
    sessionArn: str
    sessionStatus: str
    createdAt: str
    lastUpdatedAt: str
    encryptionKeyArn: Optional[str] = None
    sessionMetadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class SessionSummary(_HasResource["SessionResource"]):
    memoryId: str
    sessionExpiryTime: datetime
    sessionId: str
    sessionStartTime: datetime
    summaryText: str
    _factory: Optional[Callable[[], "SessionResource"]] = field(default=None, repr=False, compare=False)


# -- Memory readout ---------------------------------------------------------


@dataclass
class MemoryContent(_HasResource["SessionResource"]):
    sessionSummary: SessionSummary
    _factory: Optional[Callable[[], "SessionResource"]] = field(default=None, repr=False, compare=False)


@dataclass
class MemoryContents(_HasResource["SessionResource"]):
    memoryContents: List[MemoryContent]
    nextToken: Optional[str] = None
    _factory: Optional[Callable[[], "SessionResource"]] = field(default=None, repr=False, compare=False)


@dataclass
class MemorySession:  # noqa: D101
    memory_id: str
    memory_arn: str
    memory_name: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class MemorySessionSummary(_HasResource["MemorySessionResource"]):
    memory_id: str
    memory_name: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    description: Optional[str] = None
    _factory: Optional[Callable[[], "MemorySessionResource"]] = field(default=None, repr=False, compare=False)


# ===========================================================================
# 6.  Invocation (Agent & Flow) details
# ===========================================================================


@dataclass
class Invocation:  # noqa: D101
    sessionId: str
    invocationId: str
    createdAt: str


@dataclass
class InvocationSummary(_HasResource["InvocationResource"]):
    created_at: datetime
    invocation_id: str
    session_id: str
    status: str
    input_text: Optional[str] = None
    _factory: Optional[Callable[[], "InvocationResource"]] = field(default=None, repr=False, compare=False)


@dataclass
class InvocationStep:  # noqa: D101
    invocationId: str
    invocationStepId: str
    invocationStepTime: str
    payload: "Payload"
    sessionId: str


@dataclass
class InvocationStepSummary:  # noqa: D101
    invocation_step_id: str
    session_id: str
    invocation_id: str
    status: str
    created_at: datetime
    ended_at: Optional[datetime] = None
    payload: Dict[str, Any] = field(default_factory=dict)


# ===========================================================================
# 7.  Action Groups
# ===========================================================================


@dataclass
class ActionGroupExecutor:  # noqa: D101
    customControl: Literal["RETURN_CONTROL"]
    lambda_: str = field(metadata={"alias": "lambda"})


@dataclass
class S3Location:  # noqa: D101
    s3BucketName: str
    s3ObjectKey: str


@dataclass
class ApiSchema:  # noqa: D101
    payload: Optional[str] = None
    s3: Optional[S3Location] = None


@dataclass
class Parameter:  # noqa: D101
    description: str
    required: bool
    type: Literal["string", "number", "integer", "boolean", "array"]


@dataclass
class Function:  # noqa: D101
    description: str
    name: str
    parameters: Dict[str, Parameter]
    requireConfirmation: Literal["ENABLED", "DISABLED"]


@dataclass
class FunctionSchema:  # noqa: D101
    functions: List[Function]


@dataclass
class ActionGroup:  # noqa: D101
    actionGroupId: str
    actionGroupName: str
    actionGroupState: Literal["ENABLED", "DISABLED"]
    agentId: str
    agentVersion: str
    createdAt: str
    updatedAt: str
    actionGroupExecutor: Optional[ActionGroupExecutor] = None
    apiSchema: Optional[ApiSchema] = None
    clientToken: Optional[str] = None
    description: Optional[str] = None
    functionSchema: Optional[FunctionSchema] = None
    parentActionGroupSignatureParams: Dict[str, str] = field(default_factory=dict)
    parentActionSignature: Optional[
        Literal[
            "AMAZON.UserInput",
            "AMAZON.CodeInterpreter",
            "ANTHROPIC.Computer",
            "ANTHROPIC.Bash",
            "ANTHROPIC.TextEditor",
        ]
    ] = None


@dataclass
class ActionGroupSummary(_HasResource["ActionGroupResource"]):
    action_group_id: str
    action_group_name: str
    description: Optional[str] = None
    schema_arn: Optional[str] = None
    executor_arn: Optional[str] = None
    _factory: Optional[Callable[[], "ActionGroupResource"]] = field(default=None, repr=False, compare=False)


# ===========================================================================
# 8.  Rich content (images, payloads)
# ===========================================================================


@dataclass
class ImageSource:  # noqa: D101
    bytes: Optional[bytes] = None
    s3Location: Optional[Dict[str, str]] = None


@dataclass
class Image:  # noqa: D101
    format: Literal["png", "jpeg", "gif", "webp"]
    source: ImageSource


@dataclass
class ContentBlock:  # noqa: D101
    image: Optional[Image] = None
    text: Optional[str] = None


@dataclass
class Payload:  # noqa: D101
    contentBlocks: List[ContentBlock]


# ===========================================================================
# 9.  Generic *Summary helpers (used across versions & aliases)
# ===========================================================================


@dataclass
class VersionSummary(_HasResource["VersionResource"]):
    version_id: str
    version_name: str
    created_at: datetime
    description: Optional[str] = None
    _factory: Optional[Callable[[], "VersionResource"]] = field(default=None, repr=False, compare=False)


@dataclass
class AliasSummary(_HasResource["AliasResource"]):
    alias_id: str
    alias_name: str
    created_at: datetime
    metadata: Optional[str] = None
    _factory: Optional[Callable[[], "AliasResource"]] = field(default=None, repr=False, compare=False)
