import pytest
import logging
from tests.bedrock.integration.conftest import my_vcr
from fondat.aws.bedrock import agents_resource

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_list_agents.yaml")
async def test_list_agents(aws_session):
    """Test listing agents and check agent_id and agent_name."""
    ctx = aws_session
    resource = agents_resource(config_agent=ctx.config_agent)
    page = await resource.get(max_results=5)
    assert page.items is not None
    assert hasattr(page.items[0], "agent_id")
    assert hasattr(page.items[0], "agent_name")


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_get_agent.yaml")
async def test_get_agent(aws_session):
    """Test getting agent details."""
    ctx = aws_session
    resource = agents_resource(config_agent=ctx.config_agent)
    page = await resource.get(max_results=1)
    aid = page.items[0].agent_id
    agent = await resource[aid].get()
    assert agent.agent_id == aid


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_list_versions.yaml")
async def test_list_versions(aws_session):
    """Test listing agent versions."""
    ctx = aws_session
    resource = agents_resource(config_agent=ctx.config_agent)
    page = await resource.get(max_results=1)
    aid = page.items[0].agent_id
    versions = await resource[aid].versions.get(max_results=5)
    assert versions.items is not None
    assert hasattr(versions.items[0], "version_id")
    assert hasattr(versions.items[0], "version_name")


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_list_aliases.yaml")
async def test_list_aliases(aws_session):
    """Test listing agent aliases."""
    ctx = aws_session
    resource = agents_resource(config_agent=ctx.config_agent)
    page = await resource.get(max_results=1)
    aid = page.items[0].agent_id
    aliases = await resource[aid].aliases.get(max_results=5)
    assert aliases.items is not None
    assert hasattr(aliases.items[0], "alias_id")
    assert hasattr(aliases.items[0], "alias_name")


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_list_action_groups.yaml")
async def test_list_action_groups(aws_session):
    """Test listing action groups."""
    ctx = aws_session
    resource = agents_resource(config_agent=ctx.config_agent)
    page = await resource.get(max_results=1)
    aid = page.items[0].agent_id
    ag = await resource[aid].action_groups.get(agentVersion="DRAFT", max_results=5)
    assert ag.items is not None
    assert hasattr(ag.items[0], "action_group_id")
    assert hasattr(ag.items[0], "action_group_name")


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_list_collaborators.yaml")
async def test_list_collaborators(aws_session):
    """Test listing collaborators."""
    ctx = aws_session
    resource = agents_resource(config_agent=ctx.config_agent)
    page = await resource.get(max_results=1)
    aid = page.items[0].agent_id
    coll = await resource[aid].collaborators.get(agentVersion="DRAFT", max_results=5)
    assert coll.items is not None
    if coll.items:
        assert hasattr(coll.items[0], "collaborator_id")
        assert hasattr(coll.items[0], "collaborator_name")
