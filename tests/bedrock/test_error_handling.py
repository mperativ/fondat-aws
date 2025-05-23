"""Tests for bedrock error handling."""

import pytest
import fondat
import botocore.exceptions
from fondat.aws.bedrock.resources.agents import AgentsResource


async def test_list_operations_errors(mock_clients, config):
    """Test error handling in list operations."""
    agent_client, _ = mock_clients

    # Test throttling in list_flows
    agent_client.list_flows.side_effect = botocore.exceptions.ClientError(
        error_response={
            "Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"},
            "ResponseMetadata": {"HTTPStatusCode": 429},
        },
        operation_name="ListFlows",
    )
    with pytest.raises(botocore.exceptions.ClientError):
        await AgentsResource(config_agent=config, config_runtime=config)["agent-1"].flows.get()

    # Test access denied in list_aliases
    agent_client.list_agent_aliases.side_effect = botocore.exceptions.ClientError(
        error_response={
            "Error": {"Code": "AccessDeniedException"},
            "ResponseMetadata": {"HTTPStatusCode": 403},
        },
        operation_name="ListAgentAliases",
    )
    with pytest.raises(botocore.exceptions.ClientError):
        await AgentsResource(config_agent=config, config_runtime=config)[
            "agent-1"
        ].aliases.get()

    # Test validation error in list_prompts
    agent_client.list_prompts.side_effect = botocore.exceptions.ClientError(
        error_response={
            "Error": {"Code": "ValidationException"},
            "ResponseMetadata": {"HTTPStatusCode": 400},
        },
        operation_name="ListPrompts",
    )
    with pytest.raises(botocore.exceptions.ClientError):
        await AgentsResource(config_agent=config, config_runtime=config)[
            "agent-1"
        ].prompts.get()


async def test_wrap_client_error(mock_clients, config):
    """Test wrapping of AWS ClientError to Fondat errors."""
    _, runtime_client = mock_clients

    # Test BadRequestError
    runtime_client.invoke_agent.side_effect = botocore.exceptions.ClientError(
        error_response={
            "Error": {"Code": "ValidationException"},
            "ResponseMetadata": {"HTTPStatusCode": 400},
        },
        operation_name="InvokeAgent",
    )
    with pytest.raises(fondat.error.BadRequestError):
        await AgentsResource(config_agent=config, config_runtime=config)["agent-1"].invoke(
            inputText="test", sessionId="test-session", agentAliasId="alias-1"
        )

    # Test NotFoundError
    runtime_client.invoke_agent.side_effect = botocore.exceptions.ClientError(
        error_response={
            "Error": {"Code": "ResourceNotFoundException"},
            "ResponseMetadata": {"HTTPStatusCode": 404},
        },
        operation_name="InvokeAgent",
    )
    with pytest.raises(fondat.error.NotFoundError):
        await AgentsResource(config_agent=config, config_runtime=config)["agent-1"].invoke(
            inputText="test", sessionId="test-session", agentAliasId="alias-1"
        )


async def test_invoke_agent_error(mock_clients, config):
    """Test error handling for invalid agent invocation parameters."""
    _, runtime_client = mock_clients
    runtime_client.invoke_agent.side_effect = botocore.exceptions.ClientError(
        error_response={
            "Error": {"Code": "ValidationException"},
            "ResponseMetadata": {"HTTPStatusCode": 400},
        },
        operation_name="InvokeAgent",
    )
    with pytest.raises(fondat.error.BadRequestError):
        await AgentsResource(config_agent=config, config_runtime=config)["agent-1"].invoke(
            inputText="", sessionId="s1", agentAliasId="alias-1"
        )


async def test_create_session_error(mock_clients, config):
    """Test error handling for session creation conflicts."""
    _, runtime_client = mock_clients
    runtime_client.create_session.side_effect = botocore.exceptions.ClientError(
        error_response={
            "Error": {"Code": "ConflictException"},
            "ResponseMetadata": {"HTTPStatusCode": 409},
        },
        operation_name="CreateSession",
    )
    with pytest.raises(botocore.exceptions.ClientError):
        await AgentsResource(config_agent=config, config_runtime=config)[
            "agent-1"
        ].sessions.create()


async def test_invoke_flow_error(mock_clients, config):
    """Test error handling for non-existent flow invocation."""
    _, runtime_client = mock_clients
    runtime_client.invoke_flow.side_effect = botocore.exceptions.ClientError(
        error_response={
            "Error": {"Code": "ResourceNotFoundException"},
            "ResponseMetadata": {"HTTPStatusCode": 404},
        },
        operation_name="InvokeFlow",
    )
    with pytest.raises(botocore.exceptions.ClientError):
        await AgentsResource(config_agent=config, config_runtime=config)["agent-1"].flows[
            "flow1"
        ].invoke(inputText="test", flowAliasIdentifier="alias1")


async def test_memory_operations_error(mock_clients, config):
    """Test error handling for unauthorized memory operations."""
    _, runtime_client = mock_clients
    runtime_client.get_agent_memory.side_effect = botocore.exceptions.ClientError(
        error_response={
            "Error": {"Code": "AccessDeniedException"},
            "ResponseMetadata": {"HTTPStatusCode": 403},
        },
        operation_name="GetAgentMemory",
    )
    with pytest.raises(botocore.exceptions.ClientError):
        await AgentsResource(config_agent=config, config_runtime=config)["agent-1"].memory.get(
            memoryId="mid",
            agentAliasId="alias-1",
            memoryType="SESSION_SUMMARY"
        )
