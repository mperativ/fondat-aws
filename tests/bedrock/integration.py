import pytest
import json
import logging
import sys
from datetime import datetime

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
        assert "agentId" in agent and agent["agentId"], "agentId missing"
        assert "agentName" in agent and agent["agentName"]
    logger.info(f"Successfully listed {len(page.items)} agents")


@pytest.mark.asyncio
async def test_list_versions(root):
    page = await root.get(max_results=1)
    agent_id = page.items[0]["agentId"]
    versions = await root[agent_id].versions.get()
    assert versions.items, "No versions returned"
    for version in versions.items:
        assert "agentVersion" in version
    logger.info(
        f"Successfully listed {len(versions.items)} versions for agent {mask_id(agent_id)}"
    )


@pytest.mark.asyncio
async def test_session_lifecycle(root):
    page = await root.get(max_results=1)
    agent = root[page.items[0]["agentId"]]
    # create
    logger.info("Creating new session...")
    session = await agent.sessions.create()
    session_id = session["sessionId"]
    assert session["sessionStatus"] == "ACTIVE"
    logger.info(f"Session {mask_id(session_id)} created successfully")

    # list
    logger.info("Listing session invocations...")
    inv = await agent.sessions.invocations.list(session_id)
    assert isinstance(inv.items, list)
    logger.info(f"Found {len(inv.items)} invocations")

    # end then delete
    logger.info("Ending session...")
    await agent.sessions.end(session_id)
    logger.info("Session ended successfully")

    logger.info("Deleting session...")
    await agent.sessions.delete(session_id)
    logger.info("Session deleted successfully")


@pytest.mark.asyncio
async def test_list_aliases(root):
    page = await root.get(max_results=1)
    agent = root[page.items[0]["agentId"]]
    aliases = await agent.aliases.get()
    assert isinstance(aliases.items, list)
    # record alias id for later tests
    pytest.alias_id = aliases.items[0]["agentAliasId"] if aliases.items else None
    logger.info(f"Successfully listed {len(aliases.items)} aliases")


@pytest.mark.asyncio
async def test_list_action_groups(root):
    page = await root.get(max_results=1)
    agent = root[page.items[0]["agentId"]]
    groups = await agent.action_groups.get(agentVersion="DRAFT")
    assert isinstance(groups.items, list)
    logger.info(f"Successfully listed {len(groups.items)} action groups")


@pytest.mark.asyncio
async def test_list_flows(root):
    page = await root.get(max_results=1)
    agent = root[page.items[0]["agentId"]]
    flows = await agent.flows.get()
    assert isinstance(flows.items, list)
    logger.info(f"Successfully listed {len(flows.items)} flows")


@pytest.mark.asyncio
async def test_list_prompts(prompts):
    """Test listing prompts."""
    page = await prompts.get(max_results=20)
    assert page.items, "No prompts returned"
    for prompt in page.items:
        assert "id" in prompt and prompt["id"], "id missing"
        assert "name" in prompt and prompt["name"], "name missing"
        assert "description" in prompt, "description missing"
        assert "version" in prompt, "version missing"
        assert "arn" in prompt, "arn missing"
        assert "createdAt" in prompt, "createdAt missing"
        assert "updatedAt" in prompt, "updatedAt missing"
    logger.info(f"Successfully listed {len(page.items)} prompts")
    return page.items[0]["id"]  # Return first prompt ID for get_prompt test


@pytest.mark.asyncio
async def test_get_prompt(prompts):
    """Test getting a specific prompt."""
    # First get a list of prompts to find a valid ID
    page = await prompts.get(max_results=1)
    assert page.items, "No prompts available for get_prompt test"
    prompt_id = page.items[0]["id"]
    
    # Get the specific prompt
    prompt = await prompts.get_prompt(promptIdentifier=prompt_id)
    assert prompt is not None, "Prompt not found"
    assert prompt["id"] == prompt_id, "Prompt ID mismatch"
    assert "name" in prompt, "name missing"
    assert "description" in prompt, "description missing"
    assert "version" in prompt, "version missing"
    assert "arn" in prompt, "arn missing"
    assert "createdAt" in prompt, "createdAt missing"
    assert "updatedAt" in prompt, "updatedAt missing"
    assert "variants" in prompt, "variants missing"
    assert isinstance(prompt["variants"], list), "variants should be a list"
    
    # Check first variant if exists
    if prompt["variants"]:
        variant = prompt["variants"][0]
        assert "name" in variant, "variant name missing"
        assert "modelId" in variant, "variant modelId missing"
        assert "templateType" in variant, "variant templateType missing"
        assert variant["templateType"] in ["TEXT", "CHAT"], "invalid templateType"
    
    logger.info(f"Successfully retrieved prompt {mask_id(prompt_id)}")


@pytest.mark.asyncio
async def test_invoke_flow(root):
    page = await root.get(max_results=1)
    agent = root[page.items[0]["agentId"]]
    flows = await agent.flows.get()
    assert flows.items, "No flows"
    flow = next((f for f in flows.items if f["status"] == "Prepared"), None)
    if not flow:
        pytest.skip("No prepared flow to invoke")
    flow_id = flow["id"]
    logger.info(f"Found prepared flow: {mask_id(flow_id)}")

    # use alias id recorded earlier if any
    alias = getattr(pytest, "alias_id", None)
    if not alias:
        pytest.skip("No agent alias available to invoke flow")
    logger.info(f"Using alias: {mask_id(alias)}")

    logger.info("Invoking flow...")
    resp = await agent.flows[flow_id].invoke(
        inputText="Test flow invocation",
        flowAliasIdentifier=alias,
        nodeName="FlowInputNode",
        nodeOutputName="document",
    )

    # stream resp
    text = ""
    try:
        async for event in resp["responseStream"]:
            if "flowOutputEvent" in event:
                text = event["flowOutputEvent"]["content"]["document"]
    except RuntimeError:
        pass
    assert text, "Flow did not return document"
    logger.info("Flow invocation completed successfully")


@pytest.mark.asyncio
async def test_invoke_agent(root):
    page = await root.get(max_results=1)
    agent = root[page.items[0]["agentId"]]

    # Get flows to find the poetry flow
    logger.info("Getting flows...")
    flows = await agent.flows.get()
    assert flows.items, "No flows available"

    # Find the poetry flow
    flow = next((f for f in flows.items if f["status"] == "Prepared"), None)
    if not flow:
        pytest.skip("No prepared flow available")
    flow_id = flow["id"]
    logger.info(f"Found prepared flow: {mask_id(flow_id)}")

    # Get agent alias
    logger.info("Getting agent aliases...")
    aliases = await agent.aliases.get()
    assert aliases.items, "No aliases available"
    flow_alias = aliases.items[0]["agentAliasId"]
    logger.info(f"Using alias: {mask_id(flow_alias)}")

    # Create a new session
    logger.info("Creating new session...")
    session = await agent.sessions.create()
    session_id = session["sessionId"]
    assert session["sessionStatus"] == "ACTIVE", "Session should be active after creation"
    logger.info(f"Session {mask_id(session_id)} created successfully")

    try:
        # Invoke the flow
        logger.info("Invoking flow...")
        response = await agent.flows[flow_id].invoke(
            inputText="Please write a poem in English about 'The Name of the Rose'. Make it thoughtful and insightful.",
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
                        # Final output event (contains the whole document)
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
        invocations = await agent.sessions.invocations.list(session_id)
        assert isinstance(invocations.items, list), "Should be able to list session invocations"
        logger.info(f"Found {len(invocations.items)} invocations")

    finally:
        # End and delete the session
        logger.info("Ending session...")
        await agent.sessions.end(session_id)
        logger.info("Session ended successfully")

        logger.info("Deleting session...")
        await agent.sessions.delete(session_id)
        logger.info("Session deleted successfully")

        # Verify session is deleted by attempting to list invocations (should fail)
        with pytest.raises(Exception):
            await agent.sessions.invocations.list(session_id)
        logger.info("Verified session is deleted")
