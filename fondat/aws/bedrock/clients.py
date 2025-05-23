"""AWS client context managers for Bedrock operations."""

import asyncio
import logging
import fondat.aws.client

from contextlib import asynccontextmanager
from aiobotocore.client import AioBaseClient
from fondat.aws.client import Config

_logger = logging.getLogger(__name__)


async def _create(service: str, config: Config | None = None) -> asynccontextmanager:
    """Create an async context manager for an AWS service client."""
    cm = fondat.aws.client.create_client(service, config=config)
    if asyncio.iscoroutine(cm):
        cm = await cm
    return cm


@asynccontextmanager
async def agent_client(config: Config | None = None) -> AioBaseClient:
    """Asynchronous client for Bedrock Agent control-plane operations."""
    cm = await _create("bedrock-agent", config)
    async with cm as client:
        yield client


@asynccontextmanager
async def runtime_client(config: Config | None = None) -> AioBaseClient:
    """Asynchronous client for Bedrock Agent runtime operations."""
    cm = await _create("bedrock-agent-runtime", config)
    async with cm as client:
        yield client
