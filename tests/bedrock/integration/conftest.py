# tests/bedrock/integration/conftest.py
from asyncio.log import logger
import os
from pathlib import Path
import asyncio
from collections import namedtuple
import logging
from unittest.mock import AsyncMock, MagicMock
import boto3
import aiobotocore.session
import pytest
import vcr
from contextlib import asynccontextmanager

from fondat.aws.client import Config
from fondat.aws.bedrock import agents_resource, prompts_resource

class AsyncClientWrapper:
    def __init__(self, client): self._client = client
    def __getattr__(self, name):
        attr = getattr(self._client, name)
        if callable(attr):
            async def method(*a, **kw): return attr(*a, **kw)
            return method
        return attr

@pytest.fixture(autouse=True)
def patch_aiobotocore_to_boto3(monkeypatch):
    if os.environ.get("LIVE", "") == "1":
        return
    @asynccontextmanager
    async def create_sync_client(self, service_name, **kwargs):
        boto_sess = boto3.Session(
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
            region_name=kwargs.get("region_name"),
        )
        sync_client = boto_sess.client(service_name, **kwargs)
        try:
            yield AsyncClientWrapper(sync_client)
        finally:
            pass
    monkeypatch.setattr(
        aiobotocore.session.AioSession,
        "create_client",
        create_sync_client,
    )

def pytest_collection_modifyitems(items):
    """Automatically apply VCR to all tests unless marked with @pytest.mark.no_vcr"""
    for item in items:
        if not any(marker.name == 'vcr' for marker in item.iter_markers()):
            if not any(marker.name == 'no_vcr' for marker in item.iter_markers()):
                item.add_marker(pytest.mark.vcr(vcr=my_vcr))

# Configure VCR
CASSETTE_DIR = Path(__file__).parent / "cassettes" / "bedrock"
CASSETTE_DIR.mkdir(parents=True, exist_ok=True)

my_vcr = vcr.VCR(
    cassette_library_dir=str(CASSETTE_DIR),
    record_mode='once',  # Record once, then playback
    match_on=['method', 'scheme', 'host', 'port', 'path', 'query', 'body'],
    serializer='yaml',
    filter_headers=[
        ('authorization', 'DUMMY'),
        ('x-amz-security-token', 'DUMMY'),
        ('x-amz-date', 'DUMMY'),
        ('x-amz-content-sha256', 'DUMMY'),
    ],
    filter_query_parameters=[
        ('X-Amz-Security-Token', 'DUMMY'),
        ('X-Amz-Date', 'DUMMY'),
        ('X-Amz-Credential', 'DUMMY'),
        ('X-Amz-SignedHeaders', 'DUMMY'),
        ('X-Amz-Signature', 'DUMMY'),
    ],
)

AwsCtx = namedtuple("AwsCtx", "config_agent config_runtime agents prompts flows")

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def mask_id(id_str):
    """Mask sensitive identifiers with asterisks."""
    if not id_str:
        return "****"
    return "*" * len(id_str)

@pytest.fixture(scope="function")
async def aws_session(request, event_loop) -> AwsCtx:
    """
    Creates AWS configuration and resources.
    Uses VCR.py to record/replay HTTP interactions.
    """
    os.environ.setdefault("AWS_ACCESS_KEY_ID", "DUMMYID")
    os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "DUMMYSECRET")
    os.environ.setdefault("AWS_SESSION_TOKEN", "DUMMYTOKEN")
    os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-2")

    region = os.getenv("AWS_REGION", "us-east-2")
    profile = os.getenv("AWS_PROFILE", None)

    real_sess = boto3.Session(
        profile_name=profile,
        region_name=region,
    )
    orig_Session = boto3.Session
    boto3.Session = lambda *a, **k: real_sess

    cfg = Config(
        profile=profile,
        region_name=region,
    )
    agents = agents_resource(config_agent=cfg, config_runtime=cfg)
    prompts = prompts_resource(config_agent=cfg)
    page = await agents.get(max_results=1)
    agent = page.items[0]
    flows = agent.resource.flows

    try:
        yield AwsCtx(cfg, cfg, agents, prompts, flows)
    finally:
        boto3.Session = orig_Session

@pytest.fixture(scope="session")
def cfg():
    # Assumes AWS_PROFILE and SSO already configured
    return Config(region_name="us-east-2")

@pytest.fixture(scope="session")
def root(cfg):
    return agents_resource(config_agent=cfg, config_runtime=cfg)

@pytest.fixture(scope="session")
def prompts(cfg):
    return prompts_resource(config_agent=cfg)

@pytest.fixture(scope="session")
def agents(root):
    return root

@pytest.fixture(scope="session")
def agent(root):
    """Get the first active agent."""
    page = asyncio.run(root.get(max_results=1))
    assert page.items, "No agents found"
    agent_id = page.items[0].agent_id
    logger.info(f"Using agent {mask_id(agent_id)}")
    return root[agent_id]

@pytest.fixture(scope="session")
def agent_version(agent):
    """Get the first version of the agent."""
    versions = asyncio.run(agent.versions.get(max_results=1))
    assert versions.items, "No versions available"
    version = versions.items[0].version_id
    logger.info(f"Using agent version {mask_id(version)}")
    return version

@pytest.fixture(scope="session")
def agent_alias(agent):
    """Get the first alias of the agent."""
    aliases = asyncio.run(agent.aliases.get(max_results=1))
    assert aliases.items, "No aliases available"
    alias = aliases.items[0].alias_id
    logger.info(f"Using agent alias {mask_id(alias)}")
    return alias

@pytest.fixture(scope="session")
def prepared_flow(agent):
    """Get a tuple of (flow_id, alias_id) for a prepared/active flow with a valid alias."""
    flows = asyncio.run(agent.flows.get(max_results=10))
    assert flows.items, "No flows found"
    flow = flows.items[0]
    logger.info(f"Using flow: {mask_id(flow.flow_id)}")
    
    # Get aliases for this flow
    aliases = asyncio.run(agent.flows[flow.flow_id].aliases.get())
    assert aliases.items, f"No aliases found for flow {mask_id(flow.flow_id)}"
    alias = aliases.items[0]
    logger.info(f"Using alias: {mask_id(alias.alias_id)}")
    
    return (flow.flow_id, alias.alias_id)

@pytest.fixture
async def session(agent):
    """Create a session and tear it down automatically."""
    s = await agent.sessions.create()
    try:
        yield s
    finally:
        sr = agent.sessions[s.sessionId]
        await sr.end()
        await sr.delete()