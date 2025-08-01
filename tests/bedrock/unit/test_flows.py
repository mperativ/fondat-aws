import pytest
from datetime import datetime
from fondat.aws.bedrock.domain import Flow, FlowSummary
from fondat.error import NotFoundError, ForbiddenError
from fondat.aws.bedrock.resources.flows import FlowsResource, FlowResource
from tests.bedrock.unit.conftest import my_vcr
from tests.bedrock.unit.test_config import TEST_FLOW_ID


@pytest.fixture
def flows_resource(config):
    """Fixture to provide flows resource."""
    return FlowsResource(
        config_agent=config, config_runtime=config, cache_size=10, cache_expire=1
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
    """Test getting flow."""
    flow = await flow_resource.get()
    assert flow is not None

    # Validate required fields
    assert hasattr(flow, "flow_id")
    assert hasattr(flow, "flow_name")
    assert hasattr(flow, "status")
    assert hasattr(flow, "created_at")
    assert hasattr(flow, "updated_at")

    # Validate flow properties
    assert isinstance(flow.created_at, datetime)
    assert isinstance(flow.updated_at, datetime)
    assert hasattr(flow, "definition")
    assert hasattr(flow, "version")
    assert isinstance(flow, Flow)
    assert isinstance(flow.resource, FlowResource)


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


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_invoke_flow_streaming.yaml")
async def test_invoke_flow_streaming(flow_resource):
    """Test invoking a flow with streaming response."""
    try:
        aliases = await flow_resource.aliases.get(max_results=1)
        if not aliases.items:
            pytest.skip("No aliases available for flow")
        alias = aliases.items[0].alias_id
    
        response = await flow_resource.invoke_streaming(
            input_content="Write a short poem about testing.",
            flowAliasIdentifier=alias,
            nodeName="FlowInputNode",
            nodeOutputName="document",
        )
        
        # Verify we got a FlowStream object
        assert hasattr(response, "__aiter__"), "Response should be an async iterator"
        assert hasattr(response, "close"), "Response should have close method"
        
        # Process the stream
        events = []
        async with response as stream:
            async for event in stream:
                events.append(event)
        
        # Verify we got some events
        assert len(events) > 0, "Should receive streaming events"
        
        # Verify event structure (basic validation)
        for event in events:
            assert isinstance(event, dict), "Each event should be a dictionary"
            
    except Exception as e:
        pytest.fail(f"Failed to test flow streaming: {str(e)}")
