"""Tests for bedrock agents functionality."""

from unittest.mock import AsyncMock
from fondat.aws.bedrock.resources.agents import AgentsResource
from fondat.aws.bedrock.clients import agent_client
from fondat.pagination import Page
from fondat.aws.client import Config


async def test_agent_client_context_manager(monkeypatch):
    """Test agent client context manager functionality."""
    cm_mock = AsyncMock()
    cm_mock.__aenter__.return_value = cm_mock

    async def fake_create_client(service, config=None):
        assert service == "bedrock-agent"
        assert config.region_name == "us-west-1"
        return cm_mock

    monkeypatch.setattr("fondat.aws.client.create_client", fake_create_client)
    async with agent_client(Config(region_name="us-west-1")) as client:
        assert client is cm_mock


async def test_list_agents(mock_clients, config):
    """Test listing agents with pagination support."""
    agent_client, _ = mock_clients
    agent_client.list_agents.return_value = {
        "agentSummaries": [{"agentId": "agent-1", "agentName": "Agent 1"}],
        "nextToken": "token",
    }

    res = await AgentsResource(config_agent=config, config_runtime=config).get(max_results=1)
    assert isinstance(res, Page)
    assert len(res.items) == 1
    assert res.cursor.decode() == "token"
    agent_client.list_agents.assert_called_once_with(maxResults=1)


async def test_get_agent(mock_clients, config):
    """Test retrieving a specific agent by ID."""
    agent_client, _ = mock_clients
    agent_client.get_agent.return_value = {"agentId": "agent-1"}
    res = await AgentsResource(config_agent=config, config_runtime=config)["agent-1"].get()
    assert res["agentId"] == "agent-1"
    agent_client.get_agent.assert_called_once_with(agentId="agent-1")


async def test_prepare_agent(mock_clients, config):
    """Test agent preparation process."""
    agent_client, _ = mock_clients
    agent_client.prepare_agent.return_value = {"status": "PREPARING"}
    res = await AgentsResource(config_agent=config, config_runtime=config)["agent-1"].prepare()
    assert res["status"] == "PREPARING"
    agent_client.prepare_agent.assert_called_once_with(agentId="agent-1")
