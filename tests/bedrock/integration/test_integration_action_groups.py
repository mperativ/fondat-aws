import pytest
from tests.bedrock.integration.conftest import my_vcr


@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_list_action_groups.yaml")
@pytest.mark.asyncio
async def test_list_action_groups(aws_session):
    """Test listing action groups."""
    ctx = aws_session
    page = await ctx.agents.get(max_results=1)
    agent = page.items[0]
    action_groups = await ctx.agents[agent.agent_id].action_groups.get(agentVersion="DRAFT")
    assert action_groups.items is not None
    assert len(action_groups.items) > 0
    assert action_groups.items[0].action_group_id is not None


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_get_action_group.yaml")
async def test_get_action_group(aws_session):
    """Test getting action group details."""
    ctx = aws_session
    page = await ctx.agents.get(max_results=1)
    agent = page.items[0]
    action_groups = await ctx.agents[agent.agent_id].action_groups.get(agentVersion="DRAFT")
    action_group = (
        await ctx.agents[agent.agent_id]
        .action_groups[action_groups.items[0].action_group_id]
        .get(agentVersion="DRAFT")
    )
    assert action_group.action_group_id is not None
    assert action_group.action_group_name is not None
