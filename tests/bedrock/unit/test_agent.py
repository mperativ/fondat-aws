import pytest
from datetime import datetime
from fondat.aws.bedrock.domain import Agent
from fondat.aws.bedrock.resources.agent import AgentResource
from tests.bedrock.unit.conftest import my_vcr
from tests.bedrock.unit.test_config import TEST_AGENT_ID


@pytest.fixture
def agent_resource(config):
    """Provide an agent resource for testing."""
    return AgentResource(
        agent_id=TEST_AGENT_ID,
        config_agent=config,
    )


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_get_agent.yaml")
async def test_get_agent(agent_resource):
    """Test getting agent."""
    agent = await agent_resource.get()
    assert agent is not None
    assert isinstance(agent, Agent)
    assert isinstance(agent.resource, AgentResource)

    # Validate required fields
    assert hasattr(agent, "agent_id")
    assert hasattr(agent, "agent_name")
    assert hasattr(agent, "agent_status")
    assert hasattr(agent, "created_at")
    assert hasattr(agent, "updated_at")

    # Validate agent properties
    assert isinstance(agent, Agent)
    assert agent.agent_id == TEST_AGENT_ID
    assert isinstance(agent.created_at, datetime)
    assert isinstance(agent.updated_at, datetime)
