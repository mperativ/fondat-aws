"""Amazon Bedrock Agents SDK wrapper for Fondat
================================================

This module provides a high-level, resource-oriented wrapper around **Amazon Bedrock**
control-plane (``bedrock-agent``) and runtime (``bedrock-agent-runtime``) APIs, mapping 
AWS API actions to an *idempotent* Python coroutine decorated with ``@fondat.resource.operation``.

The resource graph is organised as follows:

.. code:: text

AgentsResource                                              # /agents
├── .get()                                                  # List agents
└── [agent_id] → AgentResource                              # /agents/{agent_id}
    ├── .get()                                              # Get agent
    ├── .invoke()                                           # Invoke agent (run-time)
    ├── versions → VersionsResource                         # /agents/{agent_id}/versions
    │   ├── .get()                                          # List agent versions
    │   └── [version_id] → AgentVersion                     # Get agent version
    ├── aliases → AliasesResource                           # /agents/{agent_id}/aliases
    │   ├── .get()                                          # List agent aliases
    │   └── [alias_id] → AgentAlias                         # Get agent alias
    ├── action_groups → ActionGroupsResource                # /agents/{agent_id}/action_groups
    │   ├── .get()                                          # List action groups
    │   └── [action_group_id] → ActionGroup                 # Get action group
    ├── collaborators → CollaboratorsResource               # /agents/{agent_id}/collaborators
    │   ├── .get()                                          # List collaborators
    │   └── [collaborator_id] → AgentCollaborator           # Get collaborator
    ├── memory → MemoryResource                             # /agents/{agent_id}/memory
    │   ├── .get()                                          # Get memory contents
    │   └── [memory_id] → MemoryResource                    # /agents/{agent_id}/memory/{memory_id}
    │       ├── .get()                                      # Get memory session
    │       └── .delete()                                   # Delete memory session
    └── sessions → SessionsResource                         # /agents/{agent_id}/sessions
        ├── .get()                                          # List sessions
        ├── .create()                                       # Create session
        └── [session_id] → SessionResource                  # /agents/{agent_id}/sessions/{session_id}
            ├── .get()                                      # Get session
            ├── .delete()                                   # Delete session
            ├── .end()                                      # End session
            ├── .update()                                   # Update session
            └── invocations → InvocationsResource           # /agents/{agent_id}/sessions/{session_id}/invocations
                ├── .get()                                  # List invocations
                ├── .create()                               # Create invocation
                └── [invocation_id] → InvocationResource    # /agents/{agent_id}/sessions/{session_id}/invocations/{invocation_id}
                    ├── .get_steps()                        # List invocation steps
                    ├── .put_step()                         # Add/update step
                    └── [step_id] → StepResource            # /agents/{agent_id}/sessions/{session_id}/invocations/{invocation_id}/steps/{step_id}
                        └── .get()                          # Get step

PromptsResource                                             # /prompts
├── .get()                                                  # List prompts
└── [id] → PromptResource                                   # /prompts/{id}
    ├── .get()                                              # Get prompt

FlowsResource                                               # /flows
├── .get()                                                  # List flows
└── [id] → FlowResource                                     # /flows/{id}
    ├── .get()                                              # Get flow
    ├── .invoke()                                           # Invoke flow (run-time)
    ├── versions → VersionsResource                         # /flows/{id}/versions
    │   ├── .get()                                          # List flow versions
    │   └── [version_id] → FlowVersion                      # Get flow version
    └── aliases → AliasesResource                           # /flows/{id}/aliases
        ├── .get()                                          # List flow aliases
        └── [alias_id] → FlowAlias                          # Get flow alias
"""

from collections.abc import Iterable

from fondat.aws.client import Config
from fondat.security import Policy

from .resources.agents import AgentsResource
from .resources.prompts import PromptsResource
from .resources.flows import FlowsResource

__all__ = ["agents_resource", "prompts_resource", "flows_resource"]


def agents_resource(
    *,
    config_agent: Config | None = None,
    config_runtime: Config | None = None,
    policies: Iterable[Policy] | None = None,
    cache_size: int = 100,
    cache_expire: int | float = 300,  # 5 minutes default
) -> AgentsResource:
    """
    Create and return the root AgentsResource bound to the supplied policies and botocore configs.

    Args:
        config_agent: Optional configuration for the Bedrock Agent control-plane client
        config_runtime: Optional configuration for the Bedrock Agent runtime client
        policies: Optional iterable of security policies to apply to each operation
        cache_size: Maximum number of items to cache
        cache_expire: Cache expiration time in seconds

    Returns:
        The root AgentsResource
    """
    return AgentsResource(
        config_agent=config_agent,
        config_runtime=config_runtime,
        policies=policies,
        cache_size=cache_size,
        cache_expire=cache_expire,
    )


def prompts_resource(
    *,
    config_agent: Config | None = None,
    policies: Iterable[Policy] | None = None,
    cache_size: int = 100,
    cache_expire: int | float = 300,  # 5 minutes default
) -> PromptsResource:
    """
    Create and return a root PromptsResource.

    Args:
        config_agent: Optional botocore Config for prompt-listing calls
        policies: Optional iterable of security policies to apply
        cache_size: Maximum number of items to cache
        cache_expire: Cache expiration time in seconds

    Returns:
        A PromptsResource instance
    """
    return PromptsResource(
        config_agent=config_agent,
        policies=policies,
        cache_size=cache_size,
        cache_expire=cache_expire,
    )


def flows_resource(
    *,
    config_agent: Config | None = None,
    config_runtime: Config | None = None,
    policies: Iterable[Policy] | None = None,
    cache_size: int = 100,
    cache_expire: int | float = 300,
) -> FlowsResource:
    """
    Create and return a root FlowsResource.
    """
    return FlowsResource(
        config_agent=config_agent,
        config_runtime=config_runtime,
        policies=policies,
        cache_size=cache_size,
        cache_expire=cache_expire,
    )
