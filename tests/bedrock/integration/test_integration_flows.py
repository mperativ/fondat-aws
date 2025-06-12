import pytest
from fondat.aws.bedrock import flows_resource
from tests.bedrock.integration.conftest import my_vcr, aws_session


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_integration_list_flows.yaml")
async def test_integration_list_flows_playback(aws_session):
    flows = flows_resource(
        config_agent=aws_session.config_agent, config_runtime=aws_session.config_runtime
    )
    page = await flows.get(max_results=1)
    assert len(page.items) > 0
    assert page.items[0].flow_id is not None
    assert page.items[0].flow_name is not None
    assert page.items[0].status is not None
    assert page.items[0].created_at is not None
    assert page.items[0].description is not None
    assert page.items[0]._factory is not None


@pytest.mark.live_only
@pytest.mark.asyncio
async def test_list_flows_live(aws_session):
    flows = flows_resource(
        config_agent=aws_session.config_agent, config_runtime=aws_session.config_runtime
    )
    page = await flows.get(max_results=1)
    assert page.items is not None
    assert page.items[0].flow_name is not None


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_get_flow_playback.yaml")
async def test_integration_get_flow_playback(aws_session):
    flows = flows_resource(
        config_agent=aws_session.config_agent, config_runtime=aws_session.config_runtime
    )
    page = await flows.get(max_results=1)
    flow = await flows[page.items[0].flow_id].get()
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
    flows = flows_resource(
        config_agent=aws_session.config_agent, config_runtime=aws_session.config_runtime
    )
    page = await flows.get(max_results=1)
    flow = await flows[page.items[0].flow_id].get()
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
    flows = flows_resource(
        config_agent=aws_session.config_agent, config_runtime=aws_session.config_runtime
    )
    page = await flows.get(max_results=1)
    flow = await flows[page.items[0].flow_id].get()
    versions = await flows[flow.flow_id].versions.get(max_results=1)
    version = await flows[flow.flow_id].versions["1"].get()
    assert version.version_id is not None
    assert version.flow_name is not None
    assert version.created_at is not None


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_get_flow_alias_playback.yaml")
async def test_get_flow_alias_playback(aws_session):
    flows = flows_resource(
        config_agent=aws_session.config_agent, config_runtime=aws_session.config_runtime
    )
    page = await flows.get(max_results=1)
    flow = await flows[page.items[0].flow_id].get()
    aliases = await flows[flow.flow_id].aliases.get(max_results=1)
    assert len(aliases.items) > 0
    assert aliases.items[0].alias_id is not None
    assert aliases.items[0].alias_name is not None
    assert aliases.items[0].created_at is not None
    assert aliases.items[0]._factory is not None
