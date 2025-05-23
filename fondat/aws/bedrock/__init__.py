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
        ├── .prepare()                  # PrepareAgent
        ├── .get_version()              # GetAgentVersion
        ├── .list_versions()            # ListAgentVersions
        ├── versions.*                  # Version management
        │   ├── .get()                  # ListAgentVersions
        │   └── .get_version()          # GetAgentVersion
        ├── aliases.*                   # Alias management
        │   ├── .get()                  # ListAgentAliases
        │   └── .get_alias()            # GetAgentAlias
        ├── action_groups.*             # Action group management
        │   ├── .get()                  # ListAgentActionGroups
        │   └── .get_action_group()     # GetAgentActionGroup
        ├── collaborators.*             # Collaborator management
        │   └── .get()                  # ListAgentCollaborators
        ├── prompts.*                   # Prompt management
        │   ├── .get()                  # ListPrompts
        │   └── .get_prompt()           # GetPrompt
        ├── flows.*                     # Flow management
        │   ├── .get()                  # ListFlows
        │   └── [flow_id] → FlowResource
        │       ├── .get()              # GetFlow
        │       ├── .get_alias()        # GetFlowAlias
        │       ├── .get_version()      # GetFlowVersion
        │       ├── .list_aliases()     # ListFlowAliases
        │       └── .list_versions()    # ListFlowVersions
        ├── memory.*                    # Memory management
        │   ├── .get()                  # GetAgentMemory
        │   └── .delete()               # DeleteAgentMemory
        ├── sessions.*                  # Session management
        │   ├── .create()               # CreateSession
        │   ├── .get()                  # GetSession
        │   ├── .delete()               # DeleteSession
        │   ├── .end()                  # EndSession
        │   ├── .update()               # UpdateSession
        │   └── invocations.*           # Invocation management
        │       ├── .create()           # CreateInvocation
        │       └── .put_step()         # PutInvocationStep
        ├── invoke()                    # InvokeAgent (runtime)
        ├── invoke_flow()               # InvokeFlow (runtime)
        └── invoke_inline_agent()       # InvokeInlineAgent (runtime)
"""

from collections.abc import Iterable
from typing import Any

from fondat.aws.client import Config
from fondat.security import Policy

from .resources.agents import AgentsResource

__all__ = ["agents_resource"]


def agents_resource(
    *,
    config_agent: Config | None = None,
    config_runtime: Config | None = None,
    policies: Iterable[Policy] | None = None,
) -> Any:
    """
    Create and return the root AgentsResource bound to the supplied policies and botocore configs.

    Args:
        config_agent: Optional configuration for the Bedrock Agent control-plane client
        config_runtime: Optional configuration for the Bedrock Agent runtime client
        policies: Optional iterable of security policies to apply to each operation

    Returns:
        The root AgentsResource
    """
    return AgentsResource(
        config_agent=config_agent,
        config_runtime=config_runtime,
        policies=policies,
    )
