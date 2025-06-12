"""Common fixtures for bedrock tests."""

from pathlib import Path
import os
import boto3
import aiobotocore.session
import pytest
from contextlib import asynccontextmanager

class AsyncClientWrapper:
    def __init__(self, client):
        self._client = client

    def __getattr__(self, name):
        attr = getattr(self._client, name)
        if callable(attr):
            async def _async(*a, **kw):
                return attr(*a, **kw)
            return _async
        return attr

@pytest.fixture(autouse=True)
def patch_aiobotocore_to_boto3(monkeypatch):
    """Patch aiobotocore to use boto3 for testing."""
    if os.getenv("LIVE") == "1":
        return

    @asynccontextmanager
    async def create_sync_client(self, service_name, **kwargs):
        sess = boto3.Session(region_name=kwargs.get("region_name"))
        try:
            yield AsyncClientWrapper(sess.client(service_name, **kwargs))
        finally:
            pass

    monkeypatch.setattr(
        aiobotocore.session.AioSession,
        "create_client",
        create_sync_client,
    ) 