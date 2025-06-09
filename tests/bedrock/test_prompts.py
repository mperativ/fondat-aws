"""Tests for bedrock prompts functionality."""

from fondat.aws.bedrock.resources.prompts import PromptsResource
from fondat.pagination import Page
from fondat.aws.bedrock.resources.agents import AgentsResource


async def test_list_prompts(mock_clients, config):
    """Test listing prompts with pagination."""
    agent_client, _ = mock_clients
    agent_client.list_prompts.return_value = {
        "promptSummaries": [
            {
                "arn": "arn:aws:bedrock:us-east-2:123456789012:prompt/p1",
                "createdAt": "2024-01-01T00:00:00Z",
                "description": "Test prompt",
                "id": "p1",
                "name": "Test",
                "updatedAt": "2024-01-01T00:00:00Z",
                "version": "v1"
            }
        ],
        "nextToken": "next_token"
    }
    page = await PromptsResource(config_agent=config).get(
        max_results=10,
        cursor="prev_token".encode()
    )
    assert isinstance(page, Page)
    assert len(page.items) == 1
    assert page.items[0].prompt_id == "p1"
    agent_client.list_prompts.assert_called_once_with(
        maxResults=10,
        nextToken="prev_token"
    )


async def test_get_prompt(mock_clients, config):
    """Test getting prompt details."""
    agent_client, _ = mock_clients
    agent_client.get_prompt.return_value = {
        "promptArn": "arn:aws:bedrock:us-east-1:123456789012:prompt/p1",
        "promptId": "p1",
        "promptName": "Test Prompt",
        "version": "1",
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-01T00:00:00Z",
        "variants": [],
        "description": "Test description"
    }

    res = await PromptsResource(config_agent=config)["p1"].get()
    assert res.promptArn == "arn:aws:bedrock:us-east-1:123456789012:prompt/p1"
    assert res.promptId == "p1"
    assert res.promptName == "Test Prompt"
    assert res.version == "1"
    assert res.description == "Test description"
    agent_client.get_prompt.assert_called_once_with(promptIdentifier="p1")


async def test_get_prompt_with_version(mock_clients, config):
    """Test getting prompt details with specific version."""
    agent_client, _ = mock_clients
    agent_client.get_prompt.return_value = {
        "promptArn": "arn:aws:bedrock:us-east-1:123456789012:prompt/p1",
        "promptId": "p1",
        "promptName": "Test Prompt",
        "version": "2",
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-01T00:00:00Z",
        "variants": [],
        "description": "Test description"
    }

    res = await PromptsResource(config_agent=config)["p1"].get(
        promptVersion="2"
    )
    assert res.promptArn == "arn:aws:bedrock:us-east-1:123456789012:prompt/p1"
    assert res.promptId == "p1"
    assert res.promptName == "Test Prompt"
    assert res.version == "2"
    assert res.description == "Test description"
    agent_client.get_prompt.assert_called_once_with(
        promptIdentifier="p1",
        promptVersion="2"
    )


async def test_list_prompt_versions(mock_clients, config):
    """Test listing prompt versions."""
    agent_client, _ = mock_clients
    agent_client.list_prompt_versions.return_value = {
        "promptVersionSummaries": [
            {
                "promptVersion": "v1",
                "versionName": "Version 1",
                "createdAt": "2024-01-01T00:00:00Z",
                "description": "First version"
            }
        ],
        "nextToken": "next_token"
    }
    
    versions = PromptsResource(config_agent=config)["p1"].versions
    page = await versions.get(max_results=10)
    
    assert isinstance(page, Page)
    assert len(page.items) == 1
    assert page.items[0].version_id == "v1"
    agent_client.list_prompt_versions.assert_called_once_with(
        promptIdentifier="p1",
        maxResults=10
    )


async def test_get_prompt_version(mock_clients, config):
    """Test retrieving a specific prompt version."""
    agent_client, _ = mock_clients
    agent_client.get_prompt_version.return_value = {
        "versionArn": "arn:aws:bedrock:us-east-1:123456789012:prompt/p1/version/v1",
        "versionId": "v1",
        "version": "1",
        "status": "ACTIVE",
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-01T00:00:00Z",
        "promptVersion": "v1",
        "promptId": "p1",
        "promptName": "Test Prompt",
        "description": "First version",
        "variants": []
    }

    versions = PromptsResource(config_agent=config)["p1"].versions
    version = await versions["v1"].get()
    assert version.versionArn == "arn:aws:bedrock:us-east-1:123456789012:prompt/p1/version/v1"
    assert version.versionId == "v1"
    assert version.version == "1"
    assert version.status == "ACTIVE"
    assert version.promptVersion == "v1"
    assert version.promptId == "p1"
    assert version.promptName == "Test Prompt"
    assert version.description == "First version"
    assert version.variants == []
    agent_client.get_prompt_version.assert_called_once_with(
        promptIdentifier="p1",
        promptVersion="v1"
    ) 