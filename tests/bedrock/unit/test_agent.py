import pytest
from datetime import datetime
from fondat.aws.bedrock.domain import Agent
from fondat.aws.bedrock.resources.agent import AgentResource
from fondat.aws.bedrock.resources.streams import AgentStream
from tests.bedrock.unit.conftest import my_vcr, force_record_vcr
from tests.bedrock.unit.test_config import TEST_AGENT_ID, TEST_AGENT_ALIAS_ID


@pytest.fixture
def agent_resource(config):
    """Provide an agent resource for testing."""
    return AgentResource(
        agent_id=TEST_AGENT_ID,
        config_agent=config,
        config_runtime=config,
    )


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_get_agent.yaml")
async def test_get_agent(agent_resource):
    """Test getting agent."""
    agent = await agent_resource.get()
    assert agent is not None
    assert isinstance(agent, Agent)
    assert isinstance(agent.resource, AgentResource)

    # Validate required fields
    assert hasattr(agent, "agent_id")
    assert hasattr(agent, "agent_name")
    assert hasattr(agent, "agent_status")
    assert hasattr(agent, "created_at")
    assert hasattr(agent, "updated_at")

    # Validate agent properties
    assert isinstance(agent, Agent)
    assert agent.agent_id == TEST_AGENT_ID
    assert isinstance(agent.created_at, datetime)
    assert isinstance(agent.updated_at, datetime)


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=force_record_vcr, cassette_name="test_invoke_agent_streaming.yaml")
async def test_invoke_agent_streaming(agent_resource):
    """Test invoking an agent with streaming response."""
    try:
        # Create a session first
        session = await agent_resource.sessions.create()
        
        response = await agent_resource.invoke_streaming(
            inputText="Write a short poem about testing.",
            sessionId=session.session_id,
            agentAliasId=TEST_AGENT_ALIAS_ID,
            enableTrace=True
        )
        
        # Verify we got an AgentStream object
        assert hasattr(response, "__aiter__"), "Response should be an async iterator"
        assert hasattr(response, "close"), "Response should have close method"
        assert isinstance(response, AgentStream), "Response should be an AgentStream"
        
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
        pytest.fail(f"Failed to test agent streaming: {str(e)}")
    finally:
        # Cleanup session
        try:
            await agent_resource.sessions[session.session_id].delete()
        except:
            pass  # Session might already be cleaned up
