"""Tests for the resource property in Summary classes."""

import pytest
from datetime import datetime
from typing import Any, Dict
from unittest.mock import AsyncMock

from fondat.aws.bedrock.domain import (
    AgentSummary,
    FlowSummary,
    PromptSummary,
    VersionSummary,
    AliasSummary,
    ActionGroupSummary,
    AgentCollaboratorSummary,
    SessionSummary,
    InvocationSummary,
    MemorySessionSummary,
)


@pytest.fixture
def mock_response() -> Dict[str, Any]:
    """Mock response for all resource get calls."""
    return {"dummy": "ok"}


@pytest.mark.asyncio
async def test_agent_summary_resource(mock_clients, mock_response):
    """Test AgentSummary.resource property."""
    # Setup mock
    bedrock_agent, _ = mock_clients
    bedrock_agent.get_agent.return_value = mock_response

    # Create summary and test resource property
    summary = AgentSummary(
        agent_id="test-agent",
        agent_name="Test Agent",
        status="ACTIVE",
        last_updated_at=datetime.now(),
    )
    mock_resource = AsyncMock()
    mock_resource.get.return_value = mock_response
    summary._factory = lambda: mock_resource

    # Test resource property
    full = await summary.resource.get()
    assert full == mock_response


@pytest.mark.asyncio
async def test_flow_summary_resource(mock_clients, mock_response):
    """Test FlowSummary.resource property."""
    # Setup mock
    bedrock_agent, _ = mock_clients
    bedrock_agent.get_flow.return_value = mock_response

    # Create summary and test resource property
    summary = FlowSummary(
        flow_id="test-flow",
        flow_name="Test Flow",
        status="ACTIVE",
        created_at=datetime.now(),
    )
    mock_resource = AsyncMock()
    mock_resource.get.return_value = mock_response
    summary._factory = lambda: mock_resource

    # Test resource property
    full = await summary.resource.get()
    assert full == mock_response


@pytest.mark.asyncio
async def test_prompt_summary_resource(mock_clients, mock_response):
    """Test PromptSummary.resource property."""
    # Setup mock
    bedrock_agent, _ = mock_clients
    bedrock_agent.get_prompt.return_value = mock_response

    # Create summary and test resource property
    summary = PromptSummary(
        prompt_id="test-prompt",
        prompt_name="Test Prompt",
        created_at=datetime.now(),
    )
    mock_resource = AsyncMock()
    mock_resource.get.return_value = mock_response
    summary._factory = lambda: mock_resource

    # Test resource property
    full = await summary.resource.get()
    assert full == mock_response


@pytest.mark.asyncio
async def test_version_summary_agent_resource(mock_clients, mock_response):
    """Test VersionSummary.resource property for agent versions."""
    # Setup mock
    bedrock_agent, _ = mock_clients
    bedrock_agent.get_agent_version.return_value = mock_response

    # Create summary and test resource property
    summary = VersionSummary(
        version_id="test-version",
        version_name="Test Version",
        created_at=datetime.now(),
    )
    mock_resource = AsyncMock()
    mock_resource.get.return_value = mock_response
    summary._factory = lambda: mock_resource

    # Test resource property
    full = await summary.resource.get()
    assert full == mock_response


@pytest.mark.asyncio
async def test_version_summary_flow_resource(mock_clients, mock_response):
    """Test VersionSummary.resource property for flow versions."""
    # Setup mock
    bedrock_agent, _ = mock_clients
    bedrock_agent.get_flow_version.return_value = mock_response

    # Create summary and test resource property
    summary = VersionSummary(
        version_id="test-version",
        version_name="Test Version",
        created_at=datetime.now(),
    )
    mock_resource = AsyncMock()
    mock_resource.get.return_value = mock_response
    summary._factory = lambda: mock_resource

    # Test resource property
    full = await summary.resource.get()
    assert full == mock_response


@pytest.mark.asyncio
async def test_alias_summary_agent_resource(mock_clients, mock_response):
    """Test AliasSummary.resource property for agent aliases."""
    # Setup mock
    bedrock_agent, _ = mock_clients
    bedrock_agent.get_agent_alias.return_value = mock_response

    # Create summary and test resource property
    summary = AliasSummary(
        alias_id="test-alias",
        alias_name="Test Alias",
        created_at=datetime.now(),
    )
    mock_resource = AsyncMock()
    mock_resource.get.return_value = mock_response
    summary._factory = lambda: mock_resource

    # Test resource property
    full = await summary.resource.get()
    assert full == mock_response


@pytest.mark.asyncio
async def test_alias_summary_flow_resource(mock_clients, mock_response):
    """Test AliasSummary.resource property for flow aliases."""
    # Setup mock
    bedrock_agent, _ = mock_clients
    bedrock_agent.get_flow_alias.return_value = mock_response

    # Create summary and test resource property
    summary = AliasSummary(
        alias_id="test-alias",
        alias_name="Test Alias",
        created_at=datetime.now(),
    )
    mock_resource = AsyncMock()
    mock_resource.get.return_value = mock_response
    summary._factory = lambda: mock_resource

    # Test resource property
    full = await summary.resource.get()
    assert full == mock_response


@pytest.mark.asyncio
async def test_action_group_summary_resource(mock_clients, mock_response):
    """Test ActionGroupSummary.resource property."""
    # Setup mock
    bedrock_agent, _ = mock_clients
    bedrock_agent.get_action_group.return_value = mock_response

    # Create summary and test resource property
    summary = ActionGroupSummary(
        action_group_id="test-action-group",
        action_group_name="Test Action Group",
    )
    mock_resource = AsyncMock()
    mock_resource.get.return_value = mock_response
    summary._factory = lambda: mock_resource

    # Test resource property
    full = await summary.resource.get()
    assert full == mock_response


@pytest.mark.asyncio
async def test_collaborator_summary_resource(mock_clients, mock_response):
    """Test AgentCollaboratorSummary.resource property."""
    # Setup mock
    bedrock_agent, _ = mock_clients
    bedrock_agent.get_agent_collaborator.return_value = mock_response

    # Create summary and test resource property
    summary = AgentCollaboratorSummary(
        agent_id="test-agent",
        collaborator_id="test-collaborator",
        collaborator_type="USER",
        created_at=datetime.now(),
    )
    mock_resource = AsyncMock()
    mock_resource.get.return_value = mock_response
    summary._factory = lambda: mock_resource

    # Test resource property
    full = await summary.resource.get()
    assert full == mock_response


@pytest.mark.asyncio
async def test_session_summary_resource(mock_clients, mock_response):
    """Test SessionSummary.resource property."""
    # Setup mock
    bedrock_agent, _ = mock_clients
    bedrock_agent.get_session.return_value = mock_response

    # Create summary and test resource property
    summary = SessionSummary(
        memory_id="test-memory",
        session_id="test-session",
        session_start_time=datetime.now(),
        session_expiry_time=datetime.now(),
        summary_text="Test summary"
    )
    mock_resource = AsyncMock()
    mock_resource.get.return_value = mock_response
    summary._factory = lambda: mock_resource

    # Test resource property
    full = await summary.resource.get()
    assert full == mock_response


@pytest.mark.asyncio
async def test_invocation_summary_resource(mock_clients, mock_response):
    """Test InvocationSummary.resource property."""
    # Setup mock
    bedrock_agent, _ = mock_clients
    bedrock_agent.get_invocation.return_value = mock_response

    # Create summary and test resource property
    summary = InvocationSummary(
        invocation_id="test-invocation",
        session_id="test-session",
        created_at=datetime.now(),
        status="ACTIVE",
        input_text="test input",
    )
    mock_resource = AsyncMock()
    mock_resource.get.return_value = mock_response
    summary._factory = lambda: mock_resource

    # Test resource property
    full = await summary.resource.get()
    assert full == mock_response


@pytest.mark.asyncio
async def test_memory_session_summary_resource(mock_clients, mock_response):
    """Test MemorySessionSummary.resource property."""
    # Setup mock
    bedrock_agent, _ = mock_clients
    bedrock_agent.get_memory.return_value = mock_response

    # Create summary and test resource property
    summary = MemorySessionSummary(
        memory_id="test-memory",
        memory_name="Test Memory",
        created_at=datetime.now(),
    )
    mock_resource = AsyncMock()
    mock_resource.get.return_value = mock_response
    summary._factory = lambda: mock_resource

    # Test resource property
    full = await summary.resource.get()
    assert full == mock_response 