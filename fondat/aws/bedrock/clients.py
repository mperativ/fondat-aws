"""AWS client context managers for Bedrock operations."""

import asyncio
import logging
import fondat.aws.client

from contextlib import asynccontextmanager
from aiobotocore.client import AioBaseClient
from fondat.aws.client import Config

_logger = logging.getLogger(__name__)


@asynccontextmanager
async def agent_client(config: Config | None = None) -> AioBaseClient:
    cm = fondat.aws.client.create_client("bedrock-agent", config=config)
    async with cm as client:
        yield client


@asynccontextmanager
async def runtime_client(config: Config | None = None) -> AioBaseClient:
    cm = fondat.aws.client.create_client("bedrock-agent-runtime", config=config)
    async with cm as client:
        yield client
