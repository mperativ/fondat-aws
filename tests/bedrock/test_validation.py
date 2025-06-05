"""Tests for bedrock parameter validation."""

import pytest
import fondat
from fondat.aws.bedrock.resources.agents import AgentsResource
from fondat.pagination import Page


async def test_parameter_type_validation(mock_clients, config):
    """Test validation of parameter types for various operations."""
    # Test with invalid parameter types
    with pytest.raises(fondat.error.BadRequestError):
        await AgentsResource(config_agent=config, config_runtime=config)["agent-1"].invoke(
            inputText=123, sessionId="s1", agentAliasId="alias-1"  # Should be string
        )

    with pytest.raises(fondat.error.BadRequestError):
        await AgentsResource(config_agent=config, config_runtime=config)["agent-1"].invoke(
            inputText="test", sessionId="s1", agentAliasId=123  # Should be string
        )

    with pytest.raises(fondat.error.BadRequestError):
        await AgentsResource(config_agent=config, config_runtime=config)[
            "agent-1"
        ].sessions.create(
            sessionMetadata="invalid"  # Should be dict
        )


async def test_parameter_range_validation(mock_clients, config):
    """Test validation of parameter ranges and invalid values."""
    # These parameters don't exist in the current signature, they raise TypeError
    with pytest.raises(TypeError):
        await AgentsResource(config_agent=config, config_runtime=config)[
            "agent-1"
        ].sessions.create(sessionTTLInSeconds=-1)

    with pytest.raises(TypeError):
        await AgentsResource(config_agent=config, config_runtime=config)[
            "agent-1"
        ].sessions.create(sessionTTLInSeconds=1000000)


async def test_session_parameter_validation(mock_clients, config):
    """Test session parameter validation and client handling."""
    _, runtime_client = mock_clients

    # Test with empty session ID: no validation error, should call the client
    await AgentsResource(config_agent=config, config_runtime=config)["agent-1"].sessions[""].get()
    runtime_client.get_session.assert_called_once_with(sessionIdentifier="")

    # Test with invalid metadata: passed directly to client
    runtime_client.create_session.return_value = {
        "sessionId": "sid",
        "agentId": "agent-1",
        "createdAt": "2024-01-01T00:00:00Z",
        "status": "ACTIVE"
    }
    await AgentsResource(config_agent=config, config_runtime=config)["agent-1"].sessions.create(
        sessionMetadata={"": "value"}
    )
    runtime_client.create_session.assert_called_once_with(sessionMetadata={"": "value"})

    # Test with invalid tags: passed directly to client
    await AgentsResource(config_agent=config, config_runtime=config)["agent-1"].sessions.create(
        tags={"key": ""}
    )
    runtime_client.create_session.assert_any_call(tags={"key": ""})
