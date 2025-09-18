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
    from fondat.aws.bedrock.resources.memory import MemoryResource
    from fondat.aws.bedrock.resources.prompts import PromptResource
    from fondat.aws.bedrock.resources.sessions import (
        InvocationResource,
        SessionResource,
        StepResource,
    )

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
class Agent(_HasResource["AgentResource"]):  # noqa: D101
    """Full detail of a Bedrock **Agent**."""

    agent_id: str
    agent_arn: Optional[str] = None
    agent_name: Optional[str] = None
    agent_status: Optional[str] = None
    agent_collaboration: Optional[str] = None
    agent_resource_role_arn: Optional[str] = None
    agent_version: Optional[str] = None
    client_token: Optional[str] = None
    created_at: Optional[datetime] = None
    custom_orchestration: Optional[Dict[str, Any]] = None
    customer_encryption_key_arn: Optional[str] = None
    description: Optional[str] = None
    failure_reasons: List[str] = field(default_factory=list)
    foundation_model: Optional[str] = None
    guardrail_configuration: Optional[Dict[str, Any]] = None
    idle_session_ttl_in_seconds: Optional[int] = None
    instruction: Optional[str] = None
    memory_configuration: Optional[Dict[str, Any]] = None
    orchestration_type: Optional[str] = None
    prepared_at: Optional[datetime] = None
    prompt_override_configuration: Optional[Dict[str, Any]] = None
    recommended_actions: List[str] = field(default_factory=list)
    updated_at: Optional[datetime] = None
    _factory: Optional[Callable[[], "AgentResource"]] = field(
        default=None, repr=False, compare=False
    )


@dataclass
class AgentSummary(_HasResource["AgentResource"]):
    """Lightweight view returned by *ListAgents*."""

    agent_id: str
    agent_name: str
    status: str
    last_updated_at: Optional[datetime] = None
    prepared_at: Optional[datetime] = None
    _factory: Optional[Callable[[], "AgentResource"]] = field(
        default=None, repr=False, compare=False
    )


# -- Agent Versions ---------------------------------------------------------


@dataclass
class AgentVersion:  # noqa: D101
    version_arn: str
    version_id: str
    version: str
    status: str
    created_at: datetime
    updated_at: datetime
    agent_id: str
    agent_name: str
    agent_status: str
    agent_version: str
    # optional extras
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
    execution_role_arn: Optional[str] = None
    version_name: Optional[str] = None
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
    agent_id: str
    collaborator_id: str
    collaborator_type: str
    created_at: datetime
    status: Optional[str] = None
    invitation_id: Optional[str] = None
    _factory: Optional[Callable[[], "CollaboratorResource"]] = field(
        default=None, repr=False, compare=False
    )


# -- Agent Invocation -------------------------------------------------------


@dataclass
class AgentInvocation:  # noqa: D101
    completion: Any  # EventStream from AWS SDK
    content_type: Optional[str] = None
    memory_id: Optional[str] = None
    session_id: Optional[str] = None
    _factory: Optional[Callable[[], "InvocationResource"]] = field(
        default=None, repr=False, compare=False
    )


# ===========================================================================
# 3.  Flow domain
# ===========================================================================


@dataclass
class Flow(_HasResource["FlowResource"]):  # noqa: D101
    flow_arn: str
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
    validations: List[Dict[str, Any]] = field(default_factory=list)
    _factory: Optional[Callable[[], "FlowResource"]] = field(
        default=None, repr=False, compare=False
    )


@dataclass
class FlowSummary(_HasResource["FlowResource"]):
    flow_id: str
    flow_name: str
    status: str
    created_at: datetime
    description: Optional[str] = None
    _factory: Optional[Callable[[], "FlowResource"]] = field(
        default=None, repr=False, compare=False
    )


# -- Flow Versions & Aliases ------------------------------------------------


@dataclass
class FlowVersion:  # noqa: D101
    version_arn: str
    version_id: str
    version: str
    status: str
    created_at: datetime
    updated_at: datetime
    flow_id: str
    flow_name: str
    flow_version: str
    definition: Dict[str, Any]
    customer_encryption_key_arn: Optional[str] = None
    description: Optional[str] = None
    execution_role_arn: Optional[str] = None
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
    execution_id: str
    response_stream: Optional[Any] = None  # EventStream


# ===========================================================================
# 4.  Prompt domain
# ===========================================================================


@dataclass
class Prompt(_HasResource["PromptResource"]):  # noqa: D101
    arn: str
    id: str
    name: str
    version: str
    variants: List[Dict[str, Any]]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    customer_encryption_key_arn: Optional[str] = None
    default_variant: Optional[str] = None
    description: Optional[str] = None
    _factory: Optional[Callable[[], "PromptResource"]] = field(
        default=None, repr=False, compare=False
    )


@dataclass
class PromptSummary(_HasResource["PromptResource"]):
    id: str
    name: str
    created_at: datetime
    description: Optional[str] = None
    _factory: Optional[Callable[[], "PromptResource"]] = field(
        default=None, repr=False, compare=False
    )


@dataclass
class PromptVersion:  # noqa: D101
    version_arn: str
    version_id: str
    version: str
    status: str
    created_at: datetime
    updated_at: datetime
    prompt_id: str
    prompt_name: str
    prompt_version: str
    variants: List[Dict[str, Any]]
    customer_encryption_key_arn: Optional[str] = None
    default_variant: Optional[str] = None
    description: Optional[str] = None


# ===========================================================================
# 5.  Session & Memory domain
# ===========================================================================


@dataclass
class Session(_HasResource["SessionResource"]):  # noqa: D101
    session_id: str
    session_arn: str
    session_status: str
    created_at: Optional[str] = None
    last_updated_at: Optional[str] = None
    encryption_key_arn: Optional[str] = None
    session_metadata: Dict[str, str] = field(default_factory=dict)
    response_metadata: Optional[Dict[str, Any]] = None
    _factory: Optional[Callable[[], "SessionResource"]] = field(
        default=None, repr=False, compare=False
    )


@dataclass
class SessionSummary(_HasResource["SessionResource"]):
    memory_id: str
    session_expiry_time: datetime
    session_id: str
    session_start_time: datetime
    summary_text: str
    _factory: Optional[Callable[[], "SessionResource"]] = field(
        default=None, repr=False, compare=False
    )


# -- Memory readout ---------------------------------------------------------


@dataclass
class MemoryContent(_HasResource["SessionResource"]):
    session_summary: SessionSummary
    _factory: Optional[Callable[[], "SessionResource"]] = field(
        default=None, repr=False, compare=False
    )


@dataclass
class MemoryContents(_HasResource["SessionResource"]):
    memory_contents: List[MemoryContent]
    next_token: Optional[str] = None
    _factory: Optional[Callable[[], "SessionResource"]] = field(
        default=None, repr=False, compare=False
    )


@dataclass
class MemorySession(_HasResource["MemoryResource"]):
    """Memory session details."""

    memory_id: str
    memory_arn: str
    memory_name: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    _factory: Optional[Callable[[], "MemoryResource"]] = field(
        default=None, repr=False, compare=False
    )


# ===========================================================================
# 6.  Invocation (Agent & Flow) details
# ===========================================================================


@dataclass
class Invocation:  # noqa: D101
    session_id: str
    invocation_id: str
    created_at: str


@dataclass
class InvocationSummary(_HasResource["InvocationResource"]):
    created_at: datetime
    invocation_id: str
    session_id: str
    status: str
    input_text: Optional[str] = None
    _factory: Optional[Callable[[], "InvocationResource"]] = field(
        default=None, repr=False, compare=False
    )


@dataclass
class InvocationStep:  # noqa: D101
    invocation_id: str
    invocation_step_id: str
    invocation_step_time: str
    payload: "Payload"
    session_id: str


@dataclass
class InvocationStepSummary(_HasResource["StepResource"]):  # noqa: D101
    invocation_step_id: str
    session_id: str
    invocation_id: str
    status: str
    created_at: datetime
    ended_at: Optional[datetime] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    _factory: Optional[Callable[[], "StepResource"]] = field(
        default=None, repr=False, compare=False
    )


# ===========================================================================
# 7.  Action Groups
# ===========================================================================


@dataclass
class ActionGroupExecutor:  # noqa: D101
    custom_control: Literal["RETURN_CONTROL"]
    lambda_: Optional[str] = field(default=None, metadata={"alias": "lambda"})


@dataclass
class S3Location:  # noqa: D101
    s3_bucket_name: str
    s3_object_key: str


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
    require_confirmation: Literal["ENABLED", "DISABLED"]


@dataclass
class FunctionSchema:  # noqa: D101
    functions: List[Function]


@dataclass
class ActionGroup(_HasResource["ActionGroupResource"]):  # noqa: D101
    action_group_id: str
    action_group_name: str
    action_group_state: Literal["ENABLED", "DISABLED"]
    agent_id: str
    agent_version: str
    created_at: str
    updated_at: str
    action_group_executor: Optional[ActionGroupExecutor] = None
    api_schema: Optional[ApiSchema] = None
    client_token: Optional[str] = None
    description: Optional[str] = None
    function_schema: Optional[FunctionSchema] = None
    parent_action_group_signature_params: Dict[str, str] = field(default_factory=dict)
    parent_action_signature: Optional[
        Literal[
            "AMAZON.UserInput",
            "AMAZON.CodeInterpreter",
            "ANTHROPIC.Computer",
            "ANTHROPIC.Bash",
            "ANTHROPIC.TextEditor",
        ]
    ] = None
    _factory: Optional[Callable[[], "ActionGroupResource"]] = field(
        default=None, repr=False, compare=False
    )


@dataclass
class ActionGroupSummary(_HasResource["ActionGroupResource"]):
    action_group_id: str
    action_group_name: str
    description: Optional[str] = None
    schema_arn: Optional[str] = None
    executor_arn: Optional[str] = None
    _factory: Optional[Callable[[], "ActionGroupResource"]] = field(
        default=None, repr=False, compare=False
    )


# ===========================================================================
# 8.  Rich content (images, payloads)
# ===========================================================================


@dataclass
class ImageSource:  # noqa: D101
    bytes: Optional[bytes] = None
    s3_location: Optional[Dict[str, str]] = None


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
    _factory: Optional[Callable[[], "VersionResource"]] = field(
        default=None, repr=False, compare=False
    )


@dataclass
class AliasSummary(_HasResource["AliasResource"]):
    alias_id: str
    alias_name: str
    created_at: datetime
    metadata: Optional[str] = None
    _factory: Optional[Callable[[], "AliasResource"]] = field(
        default=None, repr=False, compare=False
    )
