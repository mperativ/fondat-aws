"""Domain classes for Bedrock entities."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


# Agent related classes
@dataclass
class Agent:
    """Detailed information about a Bedrock agent."""
    agent_id: str
    agent_name: str
    agent_status: str
    description: Optional[str] = None
    foundation_model: Optional[str] = None
    last_updated_at: Optional[datetime] = None
    prepared_at: Optional[datetime] = None
    role_arn: Optional[str] = None
    instruction: Optional[str] = None
    action_groups: List[Dict[str, Any]] = field(default_factory=list)
    knowledge_bases: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class AgentSummary:
    """Summary information about a Bedrock agent."""
    agent_id: str
    agent_name: str
    agent_status: str
    description: Optional[str] = None
    foundation_model: Optional[str] = None
    last_updated_at: Optional[datetime] = None
    prepared_at: Optional[datetime] = None


@dataclass
class AgentVersion:
    """Information about a specific version of a Bedrock agent."""
    agent_id: str
    agent_version: str
    status: str
    created_at: datetime
    description: Optional[str] = None


@dataclass
class AgentAlias:
    """Information about an alias for a Bedrock agent."""
    agent_alias_id: str
    agent_alias_name: str
    agent_id: str
    agent_version: str
    created_at: datetime
    description: Optional[str] = None
    routing_configuration: Optional[List[Dict[str, Any]]] = None


@dataclass
class AgentCollaborator:
    """Information about an agent collaborator."""
    agent_id: str
    collaborator_id: str
    collaborator_type: str
    created_at: datetime
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AgentCollaboratorSummary:
    """Summary information about an agent collaborator."""
    agent_id: str
    collaborator_id: str
    collaborator_type: str
    created_at: datetime


# Flow related classes
@dataclass
class Flow:
    """Information about a Bedrock flow."""
    flow_id: str
    flow_name: str
    status: str
    created_at: datetime
    description: Optional[str] = None
    definition: Optional[Dict[str, Any]] = None


@dataclass
class FlowSummary:
    """Summary information about a Bedrock flow."""
    flow_id: str
    flow_name: str
    status: str
    created_at: datetime
    description: Optional[str] = None


@dataclass
class FlowAlias:
    """Information about a Bedrock flow alias."""
    flow_alias_id: str
    flow_alias_name: str
    flow_id: str
    created_at: datetime
    description: Optional[str] = None


@dataclass
class FlowInvocation:
    """Information about a Bedrock flow invocation."""
    flow_invocation_id: str
    flow_id: str
    created_at: datetime
    status: str


# Prompt related classes
@dataclass
class Prompt:
    """Information about a Bedrock prompt."""
    prompt_id: str
    prompt_name: str
    created_at: datetime
    description: Optional[str] = None
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class PromptSummary:
    """Summary information about a Bedrock prompt."""
    prompt_id: str
    prompt_name: str
    created_at: datetime
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# Version and Alias related classes
@dataclass
class Version:
    """Information about a Bedrock version."""
    version_id: str
    version_name: str
    created_at: datetime
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class VersionSummary:
    """Summary information about a Bedrock version."""
    version_id: str
    version_name: str
    created_at: datetime
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Alias:
    """Information about a Bedrock alias."""
    alias_id: str
    alias_name: str
    created_at: datetime
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AliasSummary:
    """Summary information about a Bedrock alias."""
    alias_id: str
    alias_name: str
    created_at: datetime
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# Session and Invocation related classes
@dataclass
class Session:
    """Information about a Bedrock agent session."""
    session_id: str
    agent_id: str
    created_at: datetime
    status: str
    description: Optional[str] = None
    session_state: Optional[Dict[str, Any]] = None


@dataclass
class SessionSummary:
    """Summary information about a Bedrock agent session."""
    session_id: str
    agent_id: str
    created_at: datetime
    status: str
    description: Optional[str] = None


@dataclass
class Invocation:
    """Information about a Bedrock agent invocation."""
    invocation_id: str
    session_id: str
    agent_id: str
    created_at: datetime
    status: str
    input_text: str
    output_text: Optional[str] = None
    trace: Optional[Dict[str, Any]] = None


@dataclass
class InvocationSummary:
    """Summary information about a Bedrock agent invocation."""
    invocation_id: str
    session_id: str
    created_at: datetime
    status: str
    input_text: str
    output_text: Optional[str] = None
    trace: Optional[Dict[str, Any]] = None


@dataclass
class InvocationStep:
    """Information about a step in a Bedrock agent invocation."""
    invocation_id: str
    invocation_step_id: str
    session_id: str
    created_at: datetime
    status: str
    payload: Dict[str, Any]
    trace: Optional[Dict[str, Any]] = None


@dataclass
class InvocationStepSummary:
    """Summary information about a step in a Bedrock agent invocation."""
    invocation_id: str
    invocation_step_id: str
    session_id: str
    created_at: datetime
    status: str
    payload: Dict[str, Any]
    trace: Optional[Dict[str, Any]] = None


# Action Group related classes
@dataclass
class ActionGroup:
    """Information about an action group for a Bedrock agent."""
    action_group_id: str
    action_group_name: str
    description: Optional[str] = None
    api_schema: Optional[Dict[str, Any]] = None
    action_group_executor: Optional[Dict[str, Any]] = None


@dataclass
class ActionGroupSummary:
    """Summary information about an action group for a Bedrock agent."""
    action_group_id: str
    action_group_name: str
    description: Optional[str] = None


# Memory related classes
@dataclass
class MemorySession:
    """Information about a Bedrock memory session."""
    memory_id: str
    memory_name: str
    created_at: datetime
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class MemorySessionSummary:
    """Summary information about a Bedrock memory session."""
    memory_id: str
    memory_name: str
    created_at: datetime
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None 