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
        # Use AWS_PROFILE if available to ensure valid credentials and SSO refresh
        profile = os.getenv("AWS_PROFILE")
        region = kwargs.get("region_name")
        if profile:
            sess = boto3.Session(profile_name=profile, region_name=region)
        else:
            sess = boto3.Session(region_name=region)
        try:
            yield AsyncClientWrapper(sess.client(service_name, **kwargs))
        finally:
            pass

    monkeypatch.setattr(
        aiobotocore.session.AioSession,
        "create_client",
        create_sync_client,
    )
