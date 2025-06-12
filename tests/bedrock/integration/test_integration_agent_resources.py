import pytest
import logging
from tests.bedrock.integration.conftest import my_vcr
from fondat.aws.bedrock import agents_resource

logger = logging.getLogger(__name__)

@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_list_agents.yaml")
async def test_list_agents_playback(aws_session):
    """Playback: reproduce el cassette y comprueba agent_id y agent_name."""
    ctx = await anext(aws_session)
    resource = agents_resource(config_agent=ctx.config_agent)
    page = await resource.get(max_results=5)
    assert page.items is not None
    assert hasattr(page.items[0], "agent_id")
    assert hasattr(page.items[0], "agent_name")

@pytest.mark.live_only
@pytest.mark.asyncio
async def test_list_agents_live(aws_session):
    """Live only: contra AWS real comprueba agent_id y agent_name no sean None."""
    ctx = await anext(aws_session)
    resource = agents_resource(config_agent=ctx.config_agent)
    page = await resource.get(max_results=5)
    assert page.items
    assert page.items[0].agent_id is not None
    assert page.items[0].agent_name is not None

@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_get_agent.yaml")
async def test_get_agent_playback(aws_session):
    """Playback: reproduce cassette y comprueba get() devuelve el mismo agentId."""
    ctx = await anext(aws_session)
    resource = agents_resource(config_agent=ctx.config_agent)
    page = await resource.get(max_results=1)
    aid = page.items[0].agent_id
    agent = await resource[aid].get()
    assert agent.agent_id == aid

@pytest.mark.live_only
@pytest.mark.asyncio
async def test_get_agent_live(aws_session):
    """Live only: contra AWS real comprueba get() devuelve un agentId válido."""
    ctx = await anext(aws_session)
    resource = agents_resource(config_agent=ctx.config_agent)
    page = await resource.get(max_results=1)
    aid = page.items[0].agent_id
    agent = await resource[aid].get()
    assert agent.agent_id == aid and aid is not None

@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_list_versions.yaml")
async def test_list_versions_playback(aws_session):
    """Playback: reproduce cassette y comprueba versiones."""
    ctx = await anext(aws_session)
    resource = agents_resource(config_agent=ctx.config_agent)
    page = await resource.get(max_results=1)
    aid = page.items[0].agent_id
    versions = await resource[aid].versions.get(max_results=5)
    assert versions.items is not None
    assert hasattr(versions.items[0], "version_id")
    assert hasattr(versions.items[0], "version_name")

@pytest.mark.live_only
@pytest.mark.asyncio
async def test_list_versions_live(aws_session):
    """Live only: contra AWS real comprueba versiones."""
    ctx = await anext(aws_session)
    resource = agents_resource(config_agent=ctx.config_agent)
    page = await resource.get(max_results=1)
    aid = page.items[0].agent_id
    versions = await resource[aid].versions.get(max_results=5)
    assert versions.items is not None
    if versions.items:
        assert versions.items[0].version_id is not None
    logger.info(f"Listed {len(versions.items)} versions live")

@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_list_aliases.yaml")
async def test_list_aliases_playback(aws_session):
    """Playback: reproduce cassette y comprueba aliases."""
    ctx = await anext(aws_session)
    resource = agents_resource(config_agent=ctx.config_agent)
    page = await resource.get(max_results=1)
    aid = page.items[0].agent_id
    aliases = await resource[aid].aliases.get(max_results=5)
    assert aliases.items is not None
    assert hasattr(aliases.items[0], "alias_id")
    assert hasattr(aliases.items[0], "alias_name")

@pytest.mark.live_only
@pytest.mark.asyncio
async def test_list_aliases_live(aws_session):
    """Live only: contra AWS real comprueba aliases."""
    ctx = await anext(aws_session)
    resource = agents_resource(config_agent=ctx.config_agent)
    page = await resource.get(max_results=1)
    aid = page.items[0].agent_id
    aliases = await resource[aid].aliases.get(max_results=5)
    assert aliases.items is not None
    assert hasattr(aliases.items[0], "alias_id")
    assert hasattr(aliases.items[0], "alias_name")

@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_list_action_groups.yaml")
async def test_list_action_groups_playback(aws_session):
    """Playback: reproduce cassette y comprueba action groups."""
    ctx = await anext(aws_session)
    resource = agents_resource(config_agent=ctx.config_agent)
    page = await resource.get(max_results=1)
    aid = page.items[0].agent_id
    ag = await resource[aid].action_groups.get(agentVersion="DRAFT", max_results=5)
    assert ag.items is not None
    assert hasattr(ag.items[0], "action_group_id")
    assert hasattr(ag.items[0], "action_group_name")

@pytest.mark.live_only
@pytest.mark.asyncio
async def test_list_action_groups_live(aws_session):
    """Live only: contra AWS real comprueba action groups."""
    ctx = await anext(aws_session)
    resource = agents_resource(config_agent=ctx.config_agent)
    page = await resource.get(max_results=1)
    aid = page.items[0].agent_id
    ag = await resource[aid].action_groups.get(agentVersion="DRAFT", max_results=5)
    assert ag.items is not None
    if ag.items:
        assert ag.items[0].action_group_id is not None
    logger.info(f"Listed {len(ag.items)} action groups live")

@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_list_collaborators.yaml")
async def test_list_collaborators_playback(aws_session):
    """Playback: reproduce cassette y comprueba collaborators."""
    ctx = await anext(aws_session)
    resource = agents_resource(config_agent=ctx.config_agent)
    page = await resource.get(max_results=1)
    aid = page.items[0].agent_id
    coll = await resource[aid].collaborators.get(agentVersion="DRAFT", max_results=5)
    assert coll.items is not None
    if coll.items:
        assert hasattr(coll.items[0], "collaborator_id")
        assert hasattr(coll.items[0], "collaborator_name")

@pytest.mark.live_only
@pytest.mark.asyncio
async def test_list_collaborators_live(aws_session):
    """Live only: contra AWS real comprueba collaborators."""
    ctx = await anext(aws_session)
    resource = agents_resource(config_agent=ctx.config_agent)
    page = await resource.get(max_results=1)
    aid = page.items[0].agent_id
    coll = await resource[aid].collaborators.get(agentVersion="DRAFT", max_results=5)
    assert coll.items is not None
    if coll.items:
        assert coll.items[0].collaborator_id is not None
    logger.info(f"Listed {len(coll.items)} collaborators live")

@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_list_flows.yaml")
async def test_list_flows_playback(aws_session):
    """Playback: reproduce cassette y comprueba flows."""
    ctx = await anext(aws_session)
    resource = agents_resource(config_agent=ctx.config_agent)
    page = await resource.get(max_results=1)
    aid = page.items[0].agent_id
    flows = await resource[aid].flows.get(max_results=1)
    assert flows.items is not None
    if flows.items:
        assert hasattr(flows.items[0], "flow_id")
        assert hasattr(flows.items[0], "flow_name")
    logger.info(f"Listed {len(flows.items)} flows in playback")

@pytest.mark.live_only
@pytest.mark.asyncio
async def test_list_flows_live(aws_session):
    """Live only: contra AWS real comprueba flows."""
    ctx = await anext(aws_session)
    resource = agents_resource(config_agent=ctx.config_agent)
    page = await resource.get(max_results=1)
    aid = page.items[0].agent_id
    flows = await resource[aid].flows.get(max_results=5)
    assert flows.items is not None
    if flows.items:
        assert flows.items[0].flow_id is not None
