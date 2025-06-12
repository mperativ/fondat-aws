import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch

from fondat.aws.bedrock.domain import (
    VersionSummary,
    AliasSummary,
    AgentVersion,
    AgentAlias,
)
from fondat.aws.bedrock.resources.generic_resources import (
    GenericVersionResource,
    GenericAliasResource,
    VersionResource,
    AliasResource,
)
from fondat.pagination import Page


@pytest.fixture
def mock_agent_client():
    """Mock agent client for testing."""
    with patch("fondat.aws.bedrock.resources.generic_resources.agent_client") as mock:
        mock_client = AsyncMock()
        mock.return_value.__aenter__.return_value = mock_client
        yield mock_client


@pytest.mark.asyncio
async def test_generic_version_resource_list_versions(mock_agent_client):
    """Test listing versions with GenericVersionResource."""
    # Setup
    resource = GenericVersionResource(
        parent_id="test-agent",
        id_field="agentId",
        list_method="list_agent_versions",
        get_method="get_agent_version",
        items_key="agentVersionSummaries",
    )

    mock_response = {
        "agentVersionSummaries": [
            {
                "agentVersion": "1",
                "versionName": "v1",
                "createdAt": "2024-01-01T00:00:00Z",
                "description": "Test version",
            }
        ],
        "nextToken": None,
    }
    mock_agent_client.list_agent_versions.return_value = mock_response

    # Execute
    result = await resource.get(max_results=5)

    # Verify
    assert isinstance(result, Page)
    assert len(result.items) == 1
    version = result.items[0]
    assert isinstance(version, VersionSummary)
    assert version.version_id == "1"
    assert version.version_name == "v1"
    assert isinstance(version.created_at, datetime)
    assert version.description == "Test version"


@pytest.mark.asyncio
async def test_generic_version_resource_missing_required_fields(mock_agent_client):
    """Test error handling for missing required fields in version response."""
    # Setup
    resource = VersionResource(
        parent_id="test-agent",
        version="1",
        id_field="agentId",
        get_method="get_agent_version",
        dto_type=AgentVersion,
    )

    mock_response = {
        "version_arn": "arn:test",
        # Missing required fields: version_id, version_name, created_at, updated_at
    }
    mock_agent_client.get_agent_version.return_value = mock_response

    # Execute and verify
    with pytest.raises(ValueError) as exc_info:
        await resource.get()
    assert "Missing required fields" in str(exc_info.value)


@pytest.mark.asyncio
async def test_generic_alias_resource_list_aliases(mock_agent_client):
    """Test listing aliases with GenericAliasResource."""
    # Setup
    resource = GenericAliasResource(
        parent_id="test-agent",
        id_field="agentId",
        list_method="list_agent_aliases",
        get_method="get_agent_alias",
        items_key="agentAliasSummaries",
    )

    mock_response = {
        "agentAliasSummaries": [
            {
                "agentAliasId": "alias1",
                "agentAliasName": "test-alias",
                "createdAt": "2024-01-01T00:00:00Z",
                "description": "Test alias",
            }
        ],
        "nextToken": None,
    }
    mock_agent_client.list_agent_aliases.return_value = mock_response

    # Execute
    result = await resource.get(max_results=5)

    # Verify
    assert isinstance(result, Page)
    assert len(result.items) == 1
    alias = result.items[0]
    assert isinstance(alias, AliasSummary)
    assert alias.alias_id == "alias1"
    assert alias.alias_name == "test-alias"
    assert isinstance(alias.created_at, datetime)


@pytest.mark.asyncio
async def test_generic_alias_resource_missing_required_fields(mock_agent_client):
    """Test error handling for missing required fields in alias response."""
    # Setup
    resource = AliasResource(
        parent_id="test-agent",
        alias_id="alias1",
        id_field="agentId",
        get_method="get_agent_alias",
        dto_type=AgentAlias,
    )

    mock_response = {
        "agent_alias_arn": "arn:test",
        # Missing required fields: agent_alias_id, agent_alias_name, created_at, updated_at
    }
    mock_agent_client.get_agent_alias.return_value = mock_response

    # Execute and verify
    with pytest.raises(ValueError) as exc_info:
        await resource.get()
    assert "Missing required fields" in str(exc_info.value)


@pytest.mark.asyncio
async def test_generic_version_resource_pagination(mock_agent_client):
    """Test pagination in GenericVersionResource."""
    # Setup
    resource = GenericVersionResource(
        parent_id="test-agent",
        id_field="agentId",
        list_method="list_agent_versions",
        get_method="get_agent_version",
        items_key="agentVersionSummaries",
    )

    mock_response1 = {
        "agentVersionSummaries": [
            {
                "agentVersion": "1",
                "versionName": "v1",
                "createdAt": "2024-01-01T00:00:00Z",
            }
        ],
        "nextToken": "token1",
    }
    mock_response2 = {
        "agentVersionSummaries": [
            {
                "agentVersion": "2",
                "versionName": "v2",
                "createdAt": "2024-01-02T00:00:00Z",
            }
        ],
        "nextToken": None,
    }
    mock_agent_client.list_agent_versions.side_effect = [mock_response1, mock_response2]

    # Execute
    result1 = await resource.get(max_results=1)
    result2 = await resource.get(max_results=1, cursor=result1.cursor)

    # Verify
    assert len(result1.items) == 1
    assert result1.items[0].version_id == "1"
    assert len(result2.items) == 1
    assert result2.items[0].version_id == "2"


@pytest.mark.asyncio
async def test_generic_alias_resource_pagination(mock_agent_client):
    """Test pagination in GenericAliasResource."""
    # Setup
    resource = GenericAliasResource(
        parent_id="test-agent",
        id_field="agentId",
        list_method="list_agent_aliases",
        get_method="get_agent_alias",
        items_key="agentAliasSummaries",
    )

    mock_response1 = {
        "agentAliasSummaries": [
            {
                "agentAliasId": "alias1",
                "agentAliasName": "test-alias1",
                "createdAt": "2024-01-01T00:00:00Z",
            }
        ],
        "nextToken": "token1",
    }
    mock_response2 = {
        "agentAliasSummaries": [
            {
                "agentAliasId": "alias2",
                "agentAliasName": "test-alias2",
                "createdAt": "2024-01-02T00:00:00Z",
            }
        ],
        "nextToken": None,
    }
    mock_agent_client.list_agent_aliases.side_effect = [mock_response1, mock_response2]

    # Execute
    result1 = await resource.get(max_results=1)
    result2 = await resource.get(max_results=1, cursor=result1.cursor)

    # Verify
    assert len(result1.items) == 1
    assert result1.items[0].alias_id == "alias1"
    assert len(result2.items) == 1
    assert result2.items[0].alias_id == "alias2"


@pytest.mark.asyncio
async def test_generic_version_resource_cache(mock_agent_client):
    """Test caching in GenericVersionResource."""
    # Setup
    resource = GenericVersionResource(
        parent_id="test-agent",
        id_field="agentId",
        list_method="list_agent_versions",
        get_method="get_agent_version",
        items_key="agentVersionSummaries",
        cache_size=100,
        cache_expire=300,
    )

    mock_response = {
        "agentVersionSummaries": [
            {
                "agentVersion": "1",
                "versionName": "v1",
                "createdAt": "2024-01-01T00:00:00Z",
            }
        ],
        "nextToken": None,
    }
    mock_agent_client.list_agent_versions.return_value = mock_response

    # Execute
    result1 = await resource.get(max_results=5)
    result2 = await resource.get(max_results=5)

    # Verify
    assert result1 == result2


@pytest.mark.asyncio
async def test_generic_alias_resource_cache(mock_agent_client):
    """Test caching in GenericAliasResource."""
    # Setup
    resource = GenericAliasResource(
        parent_id="test-agent",
        id_field="agentId",
        list_method="list_agent_aliases",
        get_method="get_agent_alias",
        items_key="agentAliasSummaries",
        cache_size=100,
        cache_expire=300,
    )

    mock_response = {
        "agentAliasSummaries": [
            {
                "agentAliasId": "alias1",
                "agentAliasName": "test-alias",
                "createdAt": "2024-01-01T00:00:00Z",
            }
        ],
        "nextToken": None,
    }
    mock_agent_client.list_agent_aliases.return_value = mock_response

    # Execute
    result1 = await resource.get(max_results=5)
    result2 = await resource.get(max_results=5)

    # Verify
    assert result1 == result2
