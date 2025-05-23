"""Tests for bedrock prompts functionality."""

from fondat.aws.bedrock.resources.agents import AgentsResource
from fondat.pagination import Page


async def test_list_prompts(mock_clients, config):
    """Test listing prompts with pagination and optional prompt identifier."""
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
    page = await AgentsResource(config_agent=config, config_runtime=config)[
        "agent-1"
    ].prompts.get(
        promptIdentifier="p1",
        max_results=10,
        cursor=b"prev_token"
    )
    assert isinstance(page, Page)
    assert len(page.items) == 1
    assert page.items[0]["id"] == "p1"
    assert page.items[0]["name"] == "Test"
    assert page.items[0]["version"] == "v1"
    agent_client.list_prompts.assert_called_once_with(
        promptIdentifier="p1",
        maxResults=10,
        nextToken="prev_token"
    ) 