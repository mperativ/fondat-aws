"""Amazon Bedrock Agents SDK wrapper for Fondat
================================================

This module provides a high-level, resource-oriented wrapper around **Amazon Bedrock**
control-plane (``bedrock-agent``) and runtime (``bedrock-agent-runtime``) APIs, mapping 
AWS API actions to an *idempotent* Python coroutine decorated with ``@fondat.resource.operation``.

The resource graph is organised as follows:

.. code:: text

    AgentsResource                      # /agents
    ├── .get()                          # ListAgents
    └── [agent_id] → AgentResource      # /agents/{agent_id}
        ├── .get()                      # GetAgent
        ├── .invoke()                   # InvokeAgent (runtime)
        ├── versions.*                  # Version management
        │   ├── .get()                  # ListAgentVersions
        │   └── [version_id] → VersionResource
        │       └── .get()              # GetAgentVersion
        ├── aliases.*                   # Alias management
        │   ├── .get()                  # ListAgentAliases
        │   └── [alias_id] → AliasResource
        │       └── .get()              # GetAgentAlias
        ├── action_groups.*             # Action group management
        │   ├── .get()                  # ListAgentActionGroups
        │   └── [action_group_id] → ActionGroupResource
        │       └── .get()              # GetAgentActionGroup
        ├── collaborators.*             # Collaborator management
        │   ├── .get()                  # ListAgentCollaborators
        │   └── [collaborator_id] → CollaboratorResource
        │       └── .get()              # GetAgentCollaborator
        ├── flows.*                     # Flow management
        │   ├── .get()                  # ListFlows
        │   └── [flow_id] → FlowResource
        │       ├── .get()              # GetFlow
        │       ├── .invoke()           # InvokeFlow (runtime)
        │       ├── versions.*          # Flow version management
        │       │   ├── .get()          # ListFlowVersions
        │       │   └── [version_id] → VersionResource
        │       │       └── .get()      # GetFlowVersion
        │       └── aliases.*           # Flow alias management
        │           ├── .get()          # ListFlowAliases
        │           └── [alias_id] → AliasResource
        │               └── .get()      # GetFlowAlias
        ├── memory.*                    # Memory management
        │   ├── .get()                  # ListAgentMemory
        │   └── [memory_id] → MemorySessionResource
        │       └── .delete()           # DeleteAgentMemory
        └── sessions.*                  # Session management
            ├── .get()                  # ListSessions
            ├── .create()               # CreateSession
            └── [session_id] → SessionResource
                ├── .get()              # GetSession
                ├── .delete()           # DeleteSession
                ├── .end()              # EndSession
                ├── .update()           # UpdateSession
                └── invocations.*       # Invocation management
                    ├── .get()          # ListInvocations
                    └── [invocation_id] → InvocationResource
                        ├── .create()   # CreateInvocation
                        ├── .get_step() # GetInvocationStep
                        ├── .get_steps()# ListInvocationSteps
                        └── .put_step() # PutInvocationStep

    PromptsResource                     # /prompts
    ├── .get()                          # ListPrompts
    └── [prompt_id] → PromptResource    # /prompts/{prompt_id}
        └── .get()                      # GetPrompt
"""

from collections.abc import Iterable

from fondat.aws.client import Config
from fondat.security import Policy

from .resources.agents import AgentsResource
from .resources.prompts import PromptsResource

__all__ = ["agents_resource", "prompts_resource"]


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
