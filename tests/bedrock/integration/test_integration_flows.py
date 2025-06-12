import pytest
from tests.bedrock.integration.conftest import my_vcr, aws_session

@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_list_flows.yaml")
async def test_list_flows_playback(aws_session):
    ctx = aws_session
    resource = ctx.agents
    page = await resource.get(max_results=1)
    agent = page.items[0]
    flows = await resource[agent.agent_id].flows.get(max_results=1)
    assert len(flows.items) > 0
    assert flows.items[0].flow_id is not None
    assert flows.items[0].flow_name is not None
    assert flows.items[0].status is not None
    assert flows.items[0].created_at is not None
    assert flows.items[0].description is not None
    assert flows.items[0]._factory is not None

@pytest.mark.live_only
@pytest.mark.asyncio
async def test_list_flows_live(aws_session):
    ctx = aws_session
    resource = ctx.agents
    page = await resource.get(max_results=1)
    agent = page.items[0]
    flows = await resource[agent.agent_id].flows.get(max_results=5)
    assert flows.items is not None
    assert flows.items[0].flow_name is not None

@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_get_flow_playback.yaml")
async def test_get_flow_playback(aws_session):
    ctx = aws_session
    resource = ctx.agents
    page = await resource.get(max_results=1)
    agent = page.items[0]
    flows = await resource[agent.agent_id].flows.get(max_results=1)
    flow = await resource[agent.agent_id].flows[flows.items[0].flow_id].get()
    assert flow.flow_id is not None
    assert flow.flow_name is not None
    assert flow.status is not None
    assert flow.created_at is not None
    assert flow.updated_at is not None
    assert flow.definition is not None
    assert flow.version is not None
    assert flow._factory is not None

@pytest.mark.live_only
@pytest.mark.asyncio
async def test_get_flow_live(aws_session):
    ctx = aws_session
    resource = ctx.agents
    page = await resource.get(max_results=1)
    agent = page.items[0]
    flows = await resource[agent.agent_id].flows.get(max_results=1)
    flow = await resource[agent.agent_id].flows[flows.items[0].flow_id].get()
    assert flow.flow_id is not None
    assert flow.flow_name is not None
    assert flow.status is not None
    assert flow.created_at is not None
    assert flow.updated_at is not None
    assert flow.definition is not None
    assert flow.version is not None
    assert flow._factory is not None

@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_get_flow_version_playback.yaml")
async def test_get_flow_version_playback(aws_session):
    ctx = aws_session
    resource = ctx.agents
    page = await resource.get(max_results=1)
    agent = page.items[0]
    flows = await resource[agent.agent_id].flows.get(max_results=1)
    flow = await resource[agent.agent_id].flows[flows.items[0].flow_id].get()
    versions = await resource[agent.agent_id].flows[flow.flow_id].versions.get(max_results=1)
    version = await resource[agent.agent_id].flows[flow.flow_id].versions["1"].get()
    assert version.version_id is not None
    assert version.flow_name is not None
    assert version.created_at is not None

@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_get_flow_alias_playback.yaml")
async def test_get_flow_alias_playback(aws_session):
    ctx = aws_session
    resource = ctx.agents
    page = await resource.get(max_results=1)
    agent = page.items[0]
    flows = await resource[agent.agent_id].flows.get(max_results=1)
    flow = await resource[agent.agent_id].flows[flows.items[0].flow_id].get()
    aliases = await resource[agent.agent_id].flows[flow.flow_id].aliases.get(max_results=1)
    assert len(aliases.items) > 0
    assert aliases.items[0].alias_id is not None
    assert aliases.items[0].alias_name is not None
    assert aliases.items[0].created_at is not None
    assert aliases.items[0]._factory is not None
