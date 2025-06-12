"""Unit tests for flows."""

import pytest
from fondat.aws.bedrock.resources.flows import FlowsResource
from fondat.aws.bedrock.domain import Flow, FlowSummary
from fondat.pagination import Page
from fondat.error import NotFoundError, ForbiddenError
from tests.bedrock.unit.conftest import my_vcr
from tests.bedrock.unit.test_config import TEST_FLOW_ID

@pytest.fixture
def flows_resource(config):
    """Fixture to provide flows resource."""
    return FlowsResource(
        config_agent=config,
        config_runtime=config,
        cache_size=10,
        cache_expire=1
    )

@pytest.fixture
def flow_resource(flows_resource):
    """Fixture to provide a specific flow resource."""
    return flows_resource[TEST_FLOW_ID]

@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_list_flows.yaml")
async def test_list_flows(flows_resource):
    """Test listing flows for an agent."""
    try:
        page = await flows_resource.get(max_results=5)
        assert isinstance(page.items, list)
        if page.items:
            assert isinstance(page.items[0], FlowSummary)
            assert page.items[0].flow_id
            assert page.items[0].flow_name
            assert page.items[0].status
    except Exception as e:
        pytest.fail(f"Failed to list flows: {str(e)}")

@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_list_flows.yaml")
async def test_list_flows_with_cursor(flows_resource):
    """Test listing flows with cursor."""
    try:
        page1 = await flows_resource.get(max_results=5)
        if not page1.items:
            pytest.skip("No flows available")
        page2 = await flows_resource.get(max_results=5, cursor=page1.cursor)
        assert isinstance(page2.items, list)
        if page2.items:
            assert isinstance(page2.items[0], FlowSummary)
    except Exception as e:
        pytest.fail(f"Failed to list flows with cursor: {str(e)}")

@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_get_flow.yaml")
async def test_get_flow(flow_resource):
    """Test getting flow details."""
    try:
        flow = await flow_resource.get()
        assert isinstance(flow, Flow)
        assert flow.flow_id == TEST_FLOW_ID
        assert flow.flow_name
        assert hasattr(flow, 'status')
        assert hasattr(flow, 'created_at')
    except Exception as e:
        pytest.fail(f"Failed to get flow: {str(e)}")

@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_flow_properties.yaml")
async def test_flow_properties(flow_resource):
    """Test flow properties (versions, aliases)."""
    try:
        versions = flow_resource.versions
        assert versions is not None
        assert versions._parent_id == TEST_FLOW_ID
        aliases = flow_resource.aliases
        assert aliases is not None
        assert aliases._parent_id == TEST_FLOW_ID
    except Exception as e:
        pytest.fail(f"Failed to test flow properties: {str(e)}")

@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_get_nonexistent_flow.yaml")
async def test_get_nonexistent_flow(flows_resource):
    """Test getting a nonexistent flow."""
    try:
        with pytest.raises((NotFoundError, ForbiddenError)):
            await flows_resource["00000000-0000-0000-0000-000000000000"].get()
    except Exception as e:
        pytest.fail(f"Failed to test nonexistent flow: {str(e)}")

@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_flow_cache.yaml")
async def test_flow_cache(flows_resource):
    """Test flow list caching."""
    try:
        page1 = await flows_resource.get()
        page2 = await flows_resource.get()
        assert page1.items == page2.items
    except Exception as e:
        pytest.fail(f"Failed to test flow cache: {str(e)}") 