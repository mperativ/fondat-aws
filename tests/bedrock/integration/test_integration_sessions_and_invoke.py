import json
import pytest
import logging
from datetime import datetime, timezone
from tests.bedrock.integration.conftest import my_vcr
from fondat.aws.bedrock import agents_resource, flows_resource
from tests.bedrock.unit.test_config import TEST_AGENT_ID, TEST_AGENT_ALIAS_ID

logger = logging.getLogger(__name__)


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_list_sessions.yaml")
async def test_list_sessions(aws_session):
    """Test listing sessions and check sessionId field."""
    ctx = aws_session
    resource = ctx.agents

    agent_id = TEST_AGENT_ID
    # list sessions
    sessions_page = await resource[agent_id].sessions.get(max_results=5)
    assert sessions_page.items and hasattr(sessions_page.items[0], "session_id")
    logger.info(f"Found {len(sessions_page.items)} sessions")


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_session_lifecycle.yaml")
async def test_session_lifecycle(aws_session):
    """Test session lifecycle: create, list invocations, end and delete."""
    ctx = aws_session
    resource = ctx.agents
    agent_id = TEST_AGENT_ID
    # create session
    session = await resource[agent_id].sessions.create()
    assert session.session_status == "ACTIVE"
    # list invocations
    inv = await resource[agent_id].sessions[session.session_id].invocations.get()
    assert isinstance(inv.items, list)
    # end session
    await resource[agent_id].sessions[session.session_id].end()
    # delete session
    await resource[agent_id].sessions[session.session_id].delete()
    logger.info("Session lifecycle completed")


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_invoke_flow.yaml")
async def test_invoke_flow(aws_session):
    """Test invoking a flow and cleanup session."""
    resource = aws_session.agents
    agent_id = TEST_AGENT_ID
    flows = flows_resource(
        config_agent=aws_session.config_agent, config_runtime=aws_session.config_runtime
    )
    flows_page = await flows.get(max_results=5)
    flow = flows_page.items[0]
    aliases = await flows[flow.flow_id].aliases.get(max_results=1)
    alias = aliases.items[0].alias_id
    session = await resource[agent_id].sessions.create()
    try:
        response = await flows[flow.flow_id].invoke(
            input_content="Write a poem in English about 'The Name of the Rose'. Make it thoughtful and insightful.",
            flowAliasIdentifier=alias,
            nodeName="FlowInputNode",
            nodeOutputName="document",
        )
        assert hasattr(response, "response_stream"), "No response_stream on invoke"
    finally:
        sr = resource[agent_id].sessions[session.session_id]
        await sr.end()
        await sr.delete()
    logger.info("Flow invocation completed")


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_invocation_lifecycle.yaml")
async def test_invocation_lifecycle(aws_session):
    """Test invocation lifecycle: create invocation, list steps, get step details."""
    ctx = aws_session
    resource = ctx.agents
    agent_id = TEST_AGENT_ID
    # create session
    session = await resource[agent_id].sessions.create()
    try:
        # create invocation
        invocation = await resource[agent_id].sessions[session.session_id].invocations.create()
        assert invocation.invocation_id is not None
        # list steps
        invocation_resource = (
            resource[agent_id]
            .sessions[session.session_id]
            .invocations[invocation.invocation_id]
        )
        steps = await invocation_resource.get_steps()
        assert isinstance(steps.items, list)
        if steps.items:
            # get step details
            step = await invocation_resource[steps.items[0].invocation_step_id].get()
            assert step.invocation_id == invocation.invocation_id
            assert step.payload is not None
    finally:
        sr = resource[agent_id].sessions[session.session_id]
        await sr.end()
        await sr.delete()
    logger.info("Test invocation lifecycle completed")


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_invocation_steps.yaml")
async def test_invocation_steps(aws_session):
    """Test invocation steps: create invocation, list steps, get step details."""
    ctx = aws_session
    resource = ctx.agents
    agent_id = TEST_AGENT_ID
    # create session
    session = await resource[agent_id].sessions.create()
    try:
        # create invocation
        invocation = await resource[agent_id].sessions[session.session_id].invocations.create()
        assert invocation.invocation_id is not None
        # list steps
        invocation_resource = (
            resource[agent_id]
            .sessions[session.session_id]
            .invocations[invocation.invocation_id]
        )
        steps = await invocation_resource.get_steps()
        assert isinstance(steps.items, list)
        if steps.items:
            # get step details
            step = await invocation_resource[steps.items[0].invocation_step_id].get()
            assert step.invocation_id == invocation.invocation_id
            assert step.payload is not None
    finally:
        sr = resource[agent_id].sessions[session.session_id]
        await sr.end()
        await sr.delete()
    logger.info("Invocation steps completed")


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_invoke_agent.yaml")
async def test_invoke_agent(aws_session):
    """Test invoking an agent and cleanup session."""
    resource = aws_session.agents
    agent_id = TEST_AGENT_ID
    alias = TEST_AGENT_ALIAS_ID
    session = await resource[agent_id].sessions.create()
    try:
        response = await resource[agent_id].invoke(
            inputText="Write a poem about the sun.",
            sessionId=session.session_id,
            agentAliasId=alias,
            enableTrace=True
        )
        assert hasattr(response, "completion"), "No completion in response"
        assert response.session_id == session.session_id
    finally:
        # Cleanup
        sr = resource[agent_id].sessions[session.session_id]
        await sr.end()
        await sr.delete()
    logger.info("Agent invocation completed")
