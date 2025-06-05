import pytest
import json
import logging
import sys
from datetime import datetime

from fondat.pagination import Page
from fondat.aws.bedrock.domain import FlowSummary
from fondat.aws.bedrock import agents_resource, prompts_resource
from fondat.aws.client import Config

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create console handler with formatting
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
console_handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(console_handler)


def mask_id(id_str):
    """Mask sensitive identifiers with asterisks."""
    if not id_str:
        return "****"
    return "*" * len(id_str)


# Helper for JSON encoding
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


@pytest.fixture(scope="module")
def cfg():
    # Assumes AWS_PROFILE and SSO already configured
    return Config(region_name="us-east-2")


@pytest.fixture(scope="module")
def root(cfg):
    return agents_resource(config_agent=cfg, config_runtime=cfg)


@pytest.fixture(scope="module")
def prompts(cfg):
    return prompts_resource(config_agent=cfg)


@pytest.mark.asyncio
async def test_list_agents(root):
    page = await root.get(max_results=20)
    assert page.items, "No agents returned"
    for agent in page.items:
        assert agent.agent_id, "agent_id missing"
        assert agent.agent_name
    logger.info(f"Successfully listed {len(page.items)} agents")


@pytest.mark.asyncio
async def test_list_versions(root):
    page = await root.get(max_results=1)
    agent_id = page.items[0].agent_id
    versions = await root[agent_id].versions.get()
    assert versions.items, "No versions returned"
    for version in versions.items:
        assert version.version_id
    logger.info(
        f"Successfully listed {len(versions.items)} versions for agent {mask_id(agent_id)}"
    )


@pytest.mark.asyncio
async def test_session_lifecycle(root):
    page = await root.get(max_results=1)
    agent = root[page.items[0].agent_id]
    # create
    logger.info("Creating new session...")
    session = await agent.sessions.create()
    session_id = session.session_id
    assert session.status == "ACTIVE"
    logger.info(f"Session {mask_id(session_id)} created successfully")

    # list
    logger.info("Listing session invocations...")
    session_resource = agent.sessions[session_id]
    inv = await session_resource.invocations.get()
    assert isinstance(inv.items, list)
    logger.info(f"Found {len(inv.items)} invocations")

    # end then delete
    logger.info("Ending session...")
    await session_resource.end()
    logger.info("Session ended successfully")

    logger.info("Deleting session...")
    await session_resource.delete()
    logger.info("Session deleted successfully")


@pytest.mark.asyncio
async def test_list_aliases(root):
    page = await root.get(max_results=1)
    agent = root[page.items[0].agent_id]
    aliases = await agent.aliases.get()
    assert isinstance(aliases.items, list)
    # record alias id for later tests
    pytest.alias_id = aliases.items[0].alias_id if aliases.items else None
    logger.info(f"Successfully listed {len(aliases.items)} aliases")


@pytest.mark.asyncio
async def test_list_action_groups(root):
    page = await root.get(max_results=1)
    agent = root[page.items[0].agent_id]
    groups = await agent.action_groups.get(agentVersion="DRAFT")
    assert isinstance(groups.items, list)
    logger.info(f"Successfully listed {len(groups.items)} action groups")


@pytest.mark.asyncio
async def test_list_flows(root):
    """Test listing flows."""
    # Get first available agent
    page = await root.get(max_results=1)
    assert page.items, "No agents available"
    agent = root[page.items[0].agent_id]

    # Get flows
    flows = await agent.flows.get(max_results=10)
    assert isinstance(flows, Page)
    
    # Debug logging
    logger.info("Flow items types:")
    for flow in flows.items:
        logger.info(f"Type: {type(flow)}, Content: {flow}")
    
    assert all(isinstance(flow, FlowSummary) for flow in flows.items)
    
    # Log available flows and their statuses
    logger.info("Available flows:")
    for f in flows.items:
        logger.info(f"Flow {mask_id(f.flow_id)}: status={f.status}")
    
    logger.info(f"Successfully listed {len(flows.items)} flows")


@pytest.mark.asyncio
async def test_list_prompts(prompts):
    """Test listing prompts."""
    page = await prompts.get(max_results=20)
    assert page.items, "No prompts returned"
    for prompt in page.items:
        assert prompt.prompt_id, "prompt_id missing"
        assert prompt.prompt_name, "prompt_name missing"
        assert prompt.description is not None, "description missing"
        assert prompt.created_at is not None, "created_at missing"
    logger.info(f"Successfully listed {len(page.items)} prompts")
    return page.items[0].prompt_id  # Return first prompt ID for get_prompt test


@pytest.mark.asyncio
async def test_get_prompt(prompts):
    """Test getting a specific prompt."""
    # First get a list of prompts to find a valid ID
    page = await prompts.get(max_results=1)
    assert page.items, "No prompts available for get_prompt test"
    prompt_id = page.items[0].prompt_id
    
    # Get the specific prompt
    prompt = await prompts[prompt_id].get()
    assert prompt is not None, "Prompt not found"
    assert prompt.prompt_id == prompt_id, "Prompt ID mismatch"
    assert prompt.prompt_name is not None, "prompt_name missing"
    assert prompt.description is not None, "description missing"
    assert prompt.created_at is not None, "created_at missing"
    assert prompt.updated_at is not None, "updated_at missing"
    
    logger.info(f"Successfully retrieved prompt {mask_id(prompt_id)}")


@pytest.mark.asyncio
async def test_invoke_flow(root):
    """Test invoking a flow with basic input."""
    # Get first available agent
    page = await root.get(max_results=1)
    assert page.items, "No agents available"
    agent = root[page.items[0].agent_id]

    # Get flows
    flows = await agent.flows.get(max_results=10)
    assert flows.items, "No flows available"
    
    # Log available flows and their statuses
    logger.info("Available flows:")
    for f in flows.items:
        logger.info(f"Flow {mask_id(f.flow_id)}: status={f.status}")
    
    # Find a flow that can be invoked (either Prepared or Active)
    flow = next((f for f in flows.items if f.status in ["Prepared", "Active"]), None)
    if not flow:
        pytest.skip("No prepared or active flow to invoke")
    flow_id = flow.flow_id
    logger.info(f"Found flow: {mask_id(flow_id)} with status: {flow.status}")

    # Get flow alias
    aliases = await agent.aliases.get()
    assert aliases.items, "No aliases available"
    flow_alias = aliases.items[0].alias_id
    logger.info(f"Using alias: {mask_id(flow_alias)}")

    # Create a new session
    logger.info("Creating new session...")
    session = await agent.sessions.create()
    session_id = session.session_id
    assert session.status == "ACTIVE", "Session should be active after creation"
    logger.info(f"Session {mask_id(session_id)} created successfully")

    try:
        # Invoke the flow
        logger.info("Invoking flow...")
        response = await agent.flows[flow_id].invoke(
            input_content={"message": "Write a poem in English about 'The Name of the Rose'. Make it thoughtful and insightful."},
            flowAliasIdentifier=flow_alias,
            nodeName="FlowInputNode",
            nodeOutputName="document",
        )

        # Process the response stream
        text = ""
        try:
            async for event in response["responseStream"]:
                if "flowOutputEvent" in event:
                    text = event["flowOutputEvent"]["content"]["document"]
        except RuntimeError:
            pass
        assert text, "Flow did not return document"
        logger.info("Flow invocation completed successfully")

    finally:
        # Clean up session
        logger.info("Ending session...")
        session_resource = agent.sessions[session_id]
        await session_resource.end()
        logger.info("Session ended successfully")

        logger.info("Deleting session...")
        await session_resource.delete()
        logger.info("Session deleted successfully")


@pytest.mark.asyncio
async def test_invoke_agent(root):
    """Test invoking an agent with a poetry request."""
    # Get first available agent
    page = await root.get(max_results=1)
    assert page.items, "No agents available"
    agent = root[page.items[0].agent_id]

    # Get flows
    logger.info("Getting flows...")
    flows = await agent.flows.get(max_results=10)
    assert flows.items, "No flows available"
    
    # Log available flows and their statuses
    logger.info("Available flows:")
    for f in flows.items:
        logger.info(f"Flow {mask_id(f.flow_id)}: status={f.status}")
    
    # Find a flow that can be invoked (either Prepared or Active)
    flow = next((f for f in flows.items if f.status in ["Prepared", "Active"]), None)
    if not flow:
        pytest.skip("No prepared or active flow available")
    flow_id = flow.flow_id
    logger.info(f"Found flow: {mask_id(flow_id)} with status: {flow.status}")

    # Get flow alias
    aliases = await agent.aliases.get()
    assert aliases.items, "No aliases available"
    flow_alias = aliases.items[0].alias_id
    logger.info(f"Using alias: {mask_id(flow_alias)}")

    # Create a new session
    logger.info("Creating new session...")
    session = await agent.sessions.create()
    session_id = session.session_id
    assert session.status == "ACTIVE", "Session should be active after creation"
    logger.info(f"Session {mask_id(session_id)} created successfully")

    # Get session resource before try block
    session_resource = agent.sessions[session_id]

    try:
        # Invoke the flow with poetry request
        logger.info("Invoking flow...")
        response = await agent.flows[flow_id].invoke(
            input_content={"message": "Please write a poem in English about 'The Name of the Rose'. Make it thoughtful and insightful."},
            flowAliasIdentifier=flow_alias,
            nodeName="FlowInputNode",
            nodeOutputName="document",
        )

        # Process the response stream
        text = ""
        try:
            async for event in response["responseStream"]:
                if isinstance(event, dict):
                    if "completion" in event:
                        # Text chunk
                        text += event["completion"]
                    elif "flowOutputEvent" in event:
                        # Final output event
                        if (
                            "content" in event["flowOutputEvent"]
                            and "document" in event["flowOutputEvent"]["content"]
                        ):
                            text = event["flowOutputEvent"]["content"]["document"]
                    elif "error" in event:
                        pytest.fail(f"Error in response stream: {event['error']}")
        except RuntimeError:
            # Connection closed at end of stream, ignore
            pass

        assert text, "Agent did not return text response"
        assert len(text) > 100, "Response should be substantial"
        assert "rose" in text.lower(), "Response should be about the requested topic"
        logger.info("Flow invocation completed successfully")

        # Verify session is still active
        logger.info("Verifying session state...")
        invocations = await session_resource.invocations.get()
        assert isinstance(invocations.items, list), "Should be able to list session invocations"
        logger.info(f"Found {len(invocations.items)} invocations")

    finally:
        # Clean up session
        logger.info("Ending session...")
        await session_resource.end()
        logger.info("Session ended successfully")

        logger.info("Deleting session...")
        await session_resource.delete()
        logger.info("Session deleted successfully")

        # Verify session is deleted
        with pytest.raises(Exception):
            await session_resource.invocations.get()
        logger.info("Verified session is deleted")
