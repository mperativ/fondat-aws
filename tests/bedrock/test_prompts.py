"""Tests for bedrock prompts functionality."""

from fondat.aws.bedrock.resources.prompts import PromptsResource
from fondat.pagination import Page


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
    """Test retrieving a specific prompt by ID."""
    agent_client, _ = mock_clients
    agent_client.get_prompt.return_value = {
        "arn": "arn:aws:bedrock:us-east-2:123456789012:prompt/p1",
        "createdAt": "2024-01-01T00:00:00Z",
        "description": "Test prompt",
        "id": "p1",
        "name": "Test",
        "updatedAt": "2024-01-01T00:00:00Z",
        "version": "v1"
    }
    res = await PromptsResource(config_agent=config)["p1"].get()
    assert res["id"] == "p1"
    agent_client.get_prompt.assert_called_once_with(promptIdentifier="p1") 