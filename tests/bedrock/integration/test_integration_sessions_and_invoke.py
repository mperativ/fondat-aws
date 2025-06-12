import json
import pytest
import logging
from datetime import datetime, timezone
from tests.bedrock.integration.conftest import my_vcr
from fondat.aws.bedrock import agents_resource
import asyncio

logger = logging.getLogger(__name__)

# Helper to encode datetime in JSON
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_list_sessions.yaml")
async def test_list_sessions_playback(aws_session):
    """Playback: list sessions and check sessionId field"""
    ctx = aws_session
    resource = ctx.agents
    # pick first agent
    page = await resource.get(max_results=1)
    agent_id = page.items[0].agent_id
    # list sessions
    sessions_page = await resource[agent_id].sessions.get(max_results=5)
    assert sessions_page.items and hasattr(sessions_page.items[0], "session_id")
    logger.info(f"Playback - Found {len(sessions_page.items)} sessions")

@pytest.mark.live_only
@pytest.mark.asyncio
async def test_list_sessions_live(aws_session):
    """Live only: list sessions and verify sessionId is not None"""
    ctx = aws_session
    resource = ctx.agents
    page = await resource.get(max_results=1)
    agent_id = page.items[0].agent_id
    sessions_page = await resource[agent_id].sessions.get(max_results=5)
    assert sessions_page.items and hasattr(sessions_page.items[0], "session_id")
    logger.info(f"Live - Found {len(sessions_page.items)} sessions")

@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_session_lifecycle.yaml")
async def test_session_lifecycle_playback(aws_session):
    """Playback: create session, list invocations, end and delete"""
    ctx = aws_session
    resource = ctx.agents
    page = await resource.get(max_results=1)
    agent_id = page.items[0].agent_id
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
    logger.info("Playback session lifecycle completed")

@pytest.mark.live_only
@pytest.mark.asyncio
async def test_session_lifecycle_live(aws_session):
    """Live only: create session, list invocations, end and delete"""
    ctx = aws_session
    resource = ctx.agents
    page = await resource.get(max_results=1)
    agent_id = page.items[0].agent_id
    session = await resource[agent_id].sessions.create()
    assert session.session_status == "ACTIVE"
    inv = await resource[agent_id].sessions[session.session_id].invocations.get()
    assert isinstance(inv.items, list)
    sr = resource[agent_id].sessions[session.session_id]
    await sr.end()
    await sr.delete()
    logger.info("Live session lifecycle completed")


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_invoke_flow.yaml")
async def test_invoke_flow_playback(aws_session):
    "Playback: invoke flow without error"
    ctx = aws_session
    resource = ctx.agents
    # pick first agent
    page = await resource.get(max_results=1)
    agent_id = page.items[0].agent_id
    # pick first flow
    flows = await resource[agent_id].flows.get(max_results=1)
    flow = flows.items[0]
    # pick first alias
    aliases = await resource[agent_id].flows[flow.flow_id].aliases.get(max_results=1)
    alias = aliases.items[0].alias_id
    # create session
    session = await resource[agent_id].sessions.create()
    try:
        response = await resource[agent_id].flows[flow.flow_id].invoke(
            input_content="Write a poem in English about 'The Name of the Rose'. Make it thoughtful and insightful.",
            flowAliasIdentifier=alias,
            nodeName="FlowInputNode",
            nodeOutputName="document",
        )
        assert hasattr(response, "response_stream"), "No response_stream on playback invoke"
    finally:
        sr = resource[agent_id].sessions[session.session_id]
        await sr.end()
        await sr.delete()
    logger.info("Playback flow invocation completed")


@pytest.mark.live_only
@pytest.mark.asyncio
async def test_invoke_flow_live(aws_session):
    """Live only: invoke flow against real AWS and cleanup session"""
    ctx = aws_session
    resource = ctx.agents
    page = await resource.get(max_results=1)
    agent_id = page.items[0].agent_id
    flows = await resource[agent_id].flows.get(max_results=5)
    flow = flows.items[0]
    aliases = await resource[agent_id].flows[flow.flow_id].aliases.get(max_results=1)
    alias = aliases.items[0].alias_id
    session = await resource[agent_id].sessions.create()
    output = ""
    try:
        response = await resource[agent_id].flows[flow.flow_id].invoke(
            input_content="Write a poem in English about 'The Name of the Rose'. Make it thoughtful and insightful.",
            flowAliasIdentifier=alias,
            nodeName="FlowInputNode",
            nodeOutputName="document",
        )
        assert hasattr(response, "response_stream"), "No response_stream on live invoke"
    finally:
        sr = resource[agent_id].sessions[session.session_id]
        await sr.end()
        await sr.delete()
    logger.info("Live flow invocation completed")

@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_invocation_lifecycle.yaml")
async def test_invocation_lifecycle_playback(aws_session):
    """Playback: create invocation, list steps, get step details"""
    ctx = aws_session
    resource = ctx.agents
    # pick first agent
    page = await resource.get(max_results=1)
    agent_id = page.items[0].agent_id
    # create session
    session = await resource[agent_id].sessions.create()
    try:
        # create invocation
        invocation = await resource[agent_id].sessions[session.session_id].invocations.create()
        assert invocation.invocation_id is not None
        # list steps
        invocation_resource = resource[agent_id].sessions[session.session_id].invocations[invocation.invocation_id]
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
    logger.info("Playback invocation lifecycle completed")


@pytest.mark.asyncio
async def test_invocation_lifecycle_live(aws_session):
    """Live: create invocation, list steps, get step details"""
    ctx = aws_session
    resource = ctx.agents
    # pick first agent
    page = await resource.get(max_results=1)
    agent_id = page.items[0].agent_id
    # create session
    session = await resource[agent_id].sessions.create()
    try:
        # create invocation
        invocation = await resource[agent_id].sessions[session.session_id].invocations.create()
        assert invocation.invocation_id is not None
        # list steps
        invocation_resource = resource[agent_id].sessions[session.session_id].invocations[invocation.invocation_id]
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
    logger.info("Live invocation lifecycle completed")


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_invocation_steps.yaml")
async def test_invocation_steps_playback(aws_session):
    """Playback: create invocation and add steps"""
    ctx = aws_session
    resource = ctx.agents
    # pick first agent
    page = await resource.get(max_results=1)
    agent_id = page.items[0].agent_id
    # create session
    session = await resource[agent_id].sessions.create()
    try:
        # create invocation
        invocation = await resource[agent_id].sessions[session.session_id].invocations.create()
        assert invocation.invocation_id is not None
        # add step
        invocation_resource = resource[agent_id].sessions[session.session_id].invocations[invocation.invocation_id]
        step_id = await invocation_resource.put_step(
            payload={"contentBlocks": [{"text": "Test step"}]},
            invocation_step_time=datetime.now(timezone.utc),
        )
        assert step_id is not None
        # verify step was added
        step = await invocation_resource[step_id].get()
        assert step.invocation_id == invocation.invocation_id
        assert step.payload is not None
    finally:
        sr = resource[agent_id].sessions[session.session_id]
        await sr.end()
        await sr.delete()
    logger.info("Playback invocation steps completed")


@pytest.mark.asyncio
async def test_invocation_steps_live(aws_session):
    """Live: create invocation and add steps"""
    ctx = aws_session
    resource = ctx.agents
    # pick first agent
    page = await resource.get(max_results=1)
    agent_id = page.items[0].agent_id
    # create session
    session = await resource[agent_id].sessions.create()
    try:
        # create invocation
        invocation = await resource[agent_id].sessions[session.session_id].invocations.create()
        assert invocation.invocation_id is not None
        # add step
        invocation_resource = resource[agent_id].sessions[session.session_id].invocations[invocation.invocation_id]
        step_id = await invocation_resource.put_step(
            payload={"contentBlocks": [{"text": "Test step"}]},
            invocation_step_time=datetime.now(timezone.utc),
        )
        assert step_id is not None
        # verify step was added
        step = await invocation_resource[step_id].get()
        assert step.invocation_id == invocation.invocation_id
        assert step.payload is not None
    finally:
        sr = resource[agent_id].sessions[session.session_id]
        await sr.end()
        await sr.delete()
    logger.info("Live invocation steps completed")