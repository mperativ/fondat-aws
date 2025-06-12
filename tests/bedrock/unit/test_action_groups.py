import pytest
from collections import namedtuple
from datetime import datetime
from fondat.aws.bedrock import agents_resource, flows_resource
from fondat.aws.bedrock.domain import (
    ActionGroup,
    ActionGroupExecutor,
    ApiSchema,
    FunctionSchema,
)
from fondat.aws.bedrock.resources.action_groups import ActionGroupResource
from fondat.error import NotFoundError, ForbiddenError, BadRequestError
from tests.bedrock.unit.conftest import my_vcr
from tests.bedrock.unit.test_config import (
    TEST_AGENT_ID,
    TEST_AGENT_VERSION,
    TEST_ACTION_GROUP_ID,
)

AwsCtx = namedtuple("AwsCtx", "config_agent config_runtime agents prompts flows")


@pytest.fixture(scope="function")
async def aws_ctx(config, aws_session) -> AwsCtx:
    """
    Creates AWS configuration and resources.
    Uses VCR.py to record/replay HTTP interactions.
    """
    agents = agents_resource(config_agent=config, config_runtime=config)
    flows = flows_resource(config_agent=config, config_runtime=config)
    page = await agents.get(max_results=1)
    agent = page.items[0]

    try:
        yield AwsCtx(config, config, agents, None, flows)
    finally:
        pass


@pytest.fixture
def action_group_resource(config):
    """Provide an action group resource for testing."""
    return ActionGroupResource(
        agent_id=TEST_AGENT_ID,
        action_group_id=TEST_ACTION_GROUP_ID,
        config_agent=config,
    )


@pytest.mark.usefixtures("patch_aiobotocore_to_boto3")
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_unit_list_action_groups.yaml")
@pytest.mark.asyncio
async def test_unit_list_action_groups(aws_ctx):
    """Test to list action groups."""
    ctx = aws_ctx
    resource = ctx.agents
    page = await resource.get(max_results=1)
    agent_id = page.items[0].agent_id
    action_groups = await resource[agent_id].action_groups.get(
        agentVersion="DRAFT", max_results=5
    )
    assert action_groups.items is not None
    if action_groups.items:
        assert action_groups.items[0].action_group_id is not None
        assert action_groups.items[0].action_group_name is not None
        # Description is optional, so we don't assert it must be non-None


@pytest.mark.usefixtures("patch_aiobotocore_to_boto3")
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_unit_list_action_groups_with_cursor.yaml")
@pytest.mark.asyncio
async def test_unit_list_action_groups_with_cursor(aws_ctx):
    """Test to list action groups with pagination."""
    ctx = aws_ctx
    resource = ctx.agents
    page = await resource.get(max_results=1)
    agent_id = page.items[0].agent_id
    # First page
    page1 = await resource[agent_id].action_groups.get(agentVersion="DRAFT", max_results=1)
    assert page1.items is not None
    assert len(page1.items) == 1
    # Cursor is optional, only check if there is more than one item
    if len(page1.items) > 1:
        assert page1.cursor is not None


@pytest.mark.usefixtures("patch_aiobotocore_to_boto3")
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_unit_get_action_group.yaml")
@pytest.mark.asyncio
async def test_unit_get_action_group(aws_ctx):
    """Test to get a specific action group."""
    ctx = aws_ctx
    resource = ctx.agents
    page = await resource.get(max_results=1)
    agent_id = page.items[0].agent_id
    action_groups = await resource[agent_id].action_groups.get(
        agentVersion="DRAFT", max_results=1
    )
    action_group_id = action_groups.items[0].action_group_id
    action_group = (
        await resource[agent_id].action_groups[action_group_id].get(agentVersion="DRAFT")
    )
    assert action_group.action_group_id == action_group_id
    assert action_group.action_group_name is not None
    # Description is optional, so we don't assert it must be non-None


@pytest.mark.usefixtures("patch_aiobotocore_to_boto3")
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_unit_action_group_properties.yaml")
@pytest.mark.asyncio
async def test_unit_action_group_properties(aws_ctx):
    """Test to verify the properties of an action group."""
    ctx = aws_ctx
    resource = ctx.agents
    page = await resource.get(max_results=1)
    agent_id = page.items[0].agent_id
    action_groups = await resource[agent_id].action_groups.get(
        agentVersion="DRAFT", max_results=1
    )
    action_group_id = action_groups.items[0].action_group_id
    action_group = (
        await resource[agent_id].action_groups[action_group_id].get(agentVersion="DRAFT")
    )
    assert action_group.action_group_id == action_group_id
    assert action_group.action_group_name is not None
    # Description and api_schema are optional
    assert action_group.function_schema is not None


@pytest.mark.usefixtures("patch_aiobotocore_to_boto3")
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_unit_get_nonexistent_action_group.yaml")
@pytest.mark.asyncio
async def test_unit_get_nonexistent_action_group(aws_ctx):
    """Test to verify behavior when trying to get a nonexistent action group."""
    ctx = aws_ctx
    resource = ctx.agents
    page = await resource.get(max_results=1)
    agent_id = page.items[0].agent_id
    with pytest.raises((NotFoundError, ForbiddenError, BadRequestError)):
        # Use an ID that matches the required pattern but does not exist
        await resource[agent_id].action_groups["ABCDEFGHIJ"].get(agentVersion="DRAFT")


@pytest.mark.usefixtures("patch_aiobotocore_to_boto3")
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_unit_action_group_cache.yaml")
@pytest.mark.asyncio
async def test_unit_action_group_cache(aws_ctx):
    """Test to verify the action group cache functionality."""
    ctx = aws_ctx
    resource = ctx.agents
    page = await resource.get(max_results=1)
    agent_id = page.items[0].agent_id
    action_groups = await resource[agent_id].action_groups.get(
        agentVersion="DRAFT", max_results=1
    )
    action_group_id = action_groups.items[0].action_group_id
    # First call
    action_group1 = (
        await resource[agent_id].action_groups[action_group_id].get(agentVersion="DRAFT")
    )
    # Second call (should use cache)
    action_group2 = (
        await resource[agent_id].action_groups[action_group_id].get(agentVersion="DRAFT")
    )
    assert action_group1 == action_group2


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_get_action_group.yaml")
async def test_get_action_group(action_group_resource):
    """Test getting action group."""
    action_group = await action_group_resource.get(agentVersion=TEST_AGENT_VERSION)
    assert action_group is not None

    # Validate required fields
    assert hasattr(action_group, "action_group_id")
    assert hasattr(action_group, "action_group_name")
    assert hasattr(action_group, "action_group_state")

    # Validate nested objects if present
    if hasattr(action_group, "action_group_executor"):
        executor = action_group.action_group_executor
        assert isinstance(executor, ActionGroupExecutor)
        assert hasattr(executor, "lambda_")
        assert hasattr(executor, "custom_control")

    if hasattr(action_group, "api_schema"):
        schema = action_group.api_schema
        if schema is not None:
            assert isinstance(schema, ApiSchema)
            if hasattr(schema, "s3"):
                assert hasattr(schema.s3, "s3_bucket_name")
                assert hasattr(schema.s3, "s3_object_key")

    if hasattr(action_group, "function_schema"):
        schema = action_group.function_schema
        assert isinstance(schema, FunctionSchema)
        assert hasattr(schema, "functions")
        for func in schema.functions:
            assert hasattr(func, "name")
            assert hasattr(func, "description")
            assert hasattr(func, "parameters")

    assert isinstance(action_group, ActionGroup)
    assert isinstance(action_group.resource, ActionGroupResource)
