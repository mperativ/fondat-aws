"""Tests for bedrock metadata and decorators."""

from fondat.aws.bedrock.resources.agents import AgentsResource
from fondat.aws.bedrock.resources.agent import AgentResource
from fondat.aws.bedrock.resources.flows import FlowResource
from fondat.aws.bedrock.clients import runtime_client
from fondat.aws.client import Config
from unittest.mock import AsyncMock


def test_operation_decorator_metadata():
    """Test operation decorator metadata on resource methods."""
    # Check if methods are decorated with operation
    assert hasattr(AgentsResource.get, "__name__")
    # Check method names - they should be 'wrapper' after decoration
    assert AgentsResource.get.__name__ == "wrapper"


async def test_runtime_client_context_manager(monkeypatch):
    """Test runtime client context manager functionality."""
    cm_mock = AsyncMock()
    cm_mock.__aenter__.return_value = cm_mock

    async def fake_create_client(service, config=None):
        assert service == "bedrock-agent-runtime"
        assert config.region_name == "us-west-1"
        return cm_mock

    monkeypatch.setattr("fondat.aws.client.create_client", fake_create_client)
    async with runtime_client(Config(region_name="us-west-1")) as client:
        assert client is cm_mock


async def test_resource_getitem(mock_clients, config):
    """Test resource indexing and property inheritance."""
    # Test AgentsResource["id"] -> AgentResource
    agent_resource = AgentsResource(config_agent=config, config_runtime=config)["agent-1"]
    assert isinstance(agent_resource, AgentResource)
    assert agent_resource.config_agent == config
    assert agent_resource.config_runtime == config
    assert getattr(agent_resource, "policies", None) is None

    # Test FlowsResource["flowId"] -> FlowResource
    flow_resource = agent_resource.flows["flow-1"]
    assert isinstance(flow_resource, FlowResource)
    assert flow_resource.config_agent == config
    assert flow_resource.config_runtime == config
    assert getattr(flow_resource, "policies", None) is None
