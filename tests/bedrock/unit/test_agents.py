"""Unit tests for agents."""

import pytest
import vcr
from fondat.aws.bedrock.resources.agents import AgentsResource, AgentResource
from fondat.aws.bedrock.domain import Agent, AgentSummary
from fondat.pagination import Page
from fondat.error import NotFoundError, ForbiddenError
from botocore.exceptions import HTTPClientError

from tests.bedrock.unit.conftest import my_vcr
from tests.bedrock.unit.test_config import TEST_AGENT_ID

@pytest.fixture
def agents_resource(config):
    """Fixture to provide agents resource."""
    return AgentsResource(
        config_agent=config,
        config_runtime=config,
        cache_size=10,
        cache_expire=1
    )

@pytest.fixture
def agent_resource(agents_resource):
    """Fixture to provide agent resource."""
    return agents_resource[TEST_AGENT_ID]

@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_list_agents.yaml")
async def test_list_agents(agents_resource):
    """Test listing agents."""
    try:
        page = await agents_resource.get(max_results=5)
        assert isinstance(page.items, list)
        if page.items:
            assert isinstance(page.items[0], AgentSummary)
            assert page.items[0].agent_id
            assert page.items[0].agent_name
            assert page.items[0].status
            # last_updated_at and prepared_at are optional
            if page.items[0].last_updated_at is not None:
                assert isinstance(page.items[0].last_updated_at, str)
            if page.items[0].prepared_at is not None:
                assert isinstance(page.items[0].prepared_at, str)
    except Exception as e:
        pytest.fail(f"Failed to list agents: {str(e)}")

@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_list_agents.yaml")
async def test_list_agents_with_cursor(agents_resource):
    """Test listing agents with cursor."""
    try:
        # Get first page
        page1 = await agents_resource.get(max_results=5)
        if not page1.items:
            pytest.skip("No agents available")
        
        # Get second page using cursor
        page2 = await agents_resource.get(max_results=5, cursor=page1.cursor)
        assert isinstance(page2.items, list)
        # Since we're using cassettes, the second page might be the same as the first
        # We'll just verify that we got a valid response
        if page2.items:
            assert isinstance(page2.items[0], AgentSummary)
    except Exception as e:
        pytest.fail(f"Failed to list agents with cursor: {str(e)}")

@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_get_agent.yaml")
async def test_get_agent(agent_resource):
    """Test getting agent details."""
    try:
        agent = await agent_resource.get()
        assert isinstance(agent, Agent)
        assert agent.agent_id == TEST_AGENT_ID
        assert agent.agent_name
        # Verify other required fields
        assert hasattr(agent, 'agent_status')
        assert hasattr(agent, 'created_at')
        assert hasattr(agent, 'updated_at')
    except Exception as e:
        pytest.fail(f"Failed to get agent: {str(e)}")

@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_agent_properties.yaml")
async def test_agent_properties(agent_resource):
    """Test agent properties."""
    try:
        # Test versions property
        versions = agent_resource.versions
        assert versions is not None
        assert versions._parent_id == TEST_AGENT_ID

        # Test aliases property
        aliases = agent_resource.aliases
        assert aliases is not None
        assert aliases._parent_id == TEST_AGENT_ID

        # Test action_groups property
        action_groups = agent_resource.action_groups
        assert action_groups is not None
        assert action_groups._agent_id == TEST_AGENT_ID

        # Test flows property
        flows = agent_resource.flows
        assert flows is not None
        assert flows._agent_id == TEST_AGENT_ID

        # Test sessions property
        sessions = agent_resource.sessions
        assert sessions is not None
        assert sessions._agent_id == TEST_AGENT_ID

        # Test memory property
        memory = agent_resource.memory
        assert memory is not None
        assert memory._agent_id == TEST_AGENT_ID

        # Test collaborators property
        collaborators = agent_resource.collaborators
        assert collaborators is not None
        assert collaborators._agent_id == TEST_AGENT_ID
    except Exception as e:
        pytest.fail(f"Failed to test agent properties: {str(e)}")

@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_get_nonexistent_agent.yaml")
async def test_get_nonexistent_agent(agents_resource):
    """Test getting a nonexistent agent."""
    try:
        with pytest.raises((NotFoundError, ForbiddenError)):
            await agents_resource["00000000-0000-0000-0000-000000000000"].get()
    except Exception as e:
        pytest.fail(f"Failed to test nonexistent agent: {str(e)}")

@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_agent_cache.yaml")
async def test_agent_cache(agents_resource):
    """Test agent list caching."""
    try:
        # First call should hit the API
        page1 = await agents_resource.get()
        
        # Second call should use cache
        page2 = await agents_resource.get()
        
        # Results should be the same
        assert page1.items == page2.items
    except Exception as e:
        pytest.fail(f"Failed to test agent cache: {str(e)}") 