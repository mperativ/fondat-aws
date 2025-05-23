"""Shared fixtures for bedrock tests."""

import pytest
from unittest.mock import AsyncMock
from fondat.aws.client import Config
from contextlib import asynccontextmanager

@pytest.fixture
def mock_clients(monkeypatch):
    """
    Fixture to mock both control-plane and runtime clients based on service name.
    Returns a tuple (agent_client, runtime_client).
    """
    agent_client = AsyncMock()
    runtime_client = AsyncMock()

    async def fake_create_client(service: str, config=None):
        @asynccontextmanager
        async def cm():
            if service == "bedrock-agent":
                yield agent_client
            elif service == "bedrock-agent-runtime":
                yield runtime_client
            else:
                raise ValueError(f"Unexpected service: {service}")

        return cm()

    monkeypatch.setattr("fondat.aws.client.create_client", fake_create_client)
    return agent_client, runtime_client

@pytest.fixture
def config():
    """AWS client configuration."""
    return Config(region_name="us-east-2") 