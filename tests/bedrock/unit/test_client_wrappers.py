"""Tests for client wrappers in Bedrock resources."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from fondat.aws.client import Config
from fondat.aws.bedrock.clients import agent_client, runtime_client, _create


@pytest.mark.asyncio
async def test_create_client_helper():
    """Test the _create helper function."""
    mock_cm = MagicMock()
    mock_cm.__enter__ = MagicMock()
    mock_cm.__exit__ = MagicMock()

    async def fake_create_client(service, config=None):
        assert service == "test-service"
        return mock_cm

    with pytest.MonkeyPatch.context() as m:
        m.setattr("fondat.aws.client.create_client", fake_create_client)
        result = await _create("test-service")
        assert result is mock_cm

    mock_async_cm = AsyncMock()

    async def fake_create_async_client(service, config=None):
        assert service == "test-service"
        return mock_async_cm

    with pytest.MonkeyPatch.context() as m:
        m.setattr("fondat.aws.client.create_client", fake_create_async_client)
        result = await _create("test-service")
        assert result is mock_async_cm


@pytest.mark.asyncio
async def test_agent_client():
    """Test agent client context manager."""
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client

    async def fake_create_client(service, config=None):
        assert service == "bedrock-agent"
        assert isinstance(config, Config)
        assert config.region_name == "us-west-2"
        return mock_client

    with pytest.MonkeyPatch.context() as m:
        m.setattr("fondat.aws.client.create_client", fake_create_client)
        async with agent_client(Config(region_name="us-west-2")) as client:
            assert client is mock_client
            mock_client.__aexit__.assert_not_called()
        mock_client.__aexit__.assert_called_once()


@pytest.mark.asyncio
async def test_runtime_client():
    """Test runtime client context manager."""
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client

    async def fake_create_client(service, config=None):
        assert service == "bedrock-agent-runtime"
        assert isinstance(config, Config)
        assert config.region_name == "us-west-2"
        return mock_client

    with pytest.MonkeyPatch.context() as m:
        m.setattr("fondat.aws.client.create_client", fake_create_client)
        async with runtime_client(Config(region_name="us-west-2")) as client:
            assert client is mock_client
            mock_client.__aexit__.assert_not_called()
        mock_client.__aexit__.assert_called_once()


@pytest.mark.asyncio
async def test_client_error_handling():
    """Test error handling in client creation."""

    async def fake_create_client(service, config=None):
        raise ValueError("Test error")

    with pytest.MonkeyPatch.context() as m:
        m.setattr("fondat.aws.client.create_client", fake_create_client)
        with pytest.raises(ValueError, match="Test error"):
            async with agent_client(Config(region_name="us-west-2")) as client:
                pass


@pytest.mark.asyncio
async def test_client_concurrent_access():
    """Test concurrent access to clients."""
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client

    async def fake_create_client(service, config=None):
        await asyncio.sleep(0.1)
        return mock_client

    with pytest.MonkeyPatch.context() as m:
        m.setattr("fondat.aws.client.create_client", fake_create_client)

        async def use_client():
            async with agent_client(Config(region_name="us-west-2")) as client:
                return client

        tasks = [use_client() for _ in range(5)]
        results = await asyncio.gather(*tasks)

        assert all(r is mock_client for r in results)
        assert mock_client.__aenter__.call_count == 5


@pytest.mark.asyncio
async def test_client_resource_cleanup():
    """Test proper cleanup of client resources."""
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client

    async def fake_create_client(service, config=None):
        return mock_client

    with pytest.MonkeyPatch.context() as m:
        m.setattr("fondat.aws.client.create_client", fake_create_client)

        async with agent_client(Config(region_name="us-west-2")) as client:
            pass
        mock_client.__aexit__.assert_called_once()
        mock_client.__aexit__.reset_mock()
        with pytest.raises(ValueError):
            async with agent_client(Config(region_name="us-west-2")) as client:
                raise ValueError("Test error")
        mock_client.__aexit__.assert_called_once()


@pytest.mark.asyncio
async def test_client_method_propagation():
    """Test that client methods are properly propagated."""
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.test_method = AsyncMock(return_value="test result")

    async def fake_create_client(service, config=None):
        return mock_client

    with pytest.MonkeyPatch.context() as m:
        m.setattr("fondat.aws.client.create_client", fake_create_client)
        async with agent_client(Config(region_name="us-west-2")) as client:
            result = await client.test_method()
            assert result == "test result"
            mock_client.test_method.assert_called_once()
