from fondat.pagination import Page

from fondat.aws.bedrock.resources.agents import AgentsResource
from fondat.aws.bedrock.resources.versions import VersionsResource


async def test_list_agent_versions_with_generic(mock_clients, config):
    """Test listing agent versions using the generic resource."""
    agent_client, _ = mock_clients
    agent_client.list_agent_versions.return_value = {
        "agentVersionSummaries": [{
            "agentVersion": "v1",
            "versionName": "Agent Version 1",
            "createdAt": "2024-03-20T10:00:00Z"
        }],
        "nextToken": "t",
    }

    versions = VersionsResource("agent-1", config_agent=config)
    page = await versions.get(max_results=1)
    assert isinstance(page, Page)
    assert len(page.items) == 1
    assert page.items[0].version_id == "v1"
    agent_client.list_agent_versions.assert_called_once_with(
        agentId="agent-1", maxResults=1
    )


async def test_get_agent_version_with_generic(mock_clients, config):
    """Test retrieving a specific agent version using the generic resource."""
    agent_client, _ = mock_clients
    agent_client.get_agent_version.return_value = {
        "versionArn": "arn:aws:bedrock:us-east-1:123456789012:agent/a1/version/v1",
        "versionId": "v1",
        "version": "1",
        "status": "ACTIVE",
        "createdAt": "2024-03-20T10:00:00Z",
        "updatedAt": "2024-03-20T10:00:00Z",
        "agentVersion": "v1",
        "agentId": "a1",
        "agentName": "Test Agent",
        "agentStatus": "ACTIVE",
        "versionName": "Agent Version 1"
    }

    versions = VersionsResource("agent-1", config_agent=config)
    result = await versions["v1"].get()
    assert result.versionArn == "arn:aws:bedrock:us-east-1:123456789012:agent/a1/version/v1"
    assert result.versionId == "v1"
    assert result.version == "1"
    assert result.status == "ACTIVE"
    assert result.agentVersion == "v1"
    assert result.agentId == "a1"
    assert result.agentName == "Test Agent"
    assert result.agentStatus == "ACTIVE"
    assert result.versionName == "Agent Version 1"
    agent_client.get_agent_version.assert_called_once_with(
        agentId="agent-1",
        agentVersion="v1"
    ) 