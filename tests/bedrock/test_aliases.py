"""Tests for bedrock aliases and collaborators functionality."""

from fondat.aws.bedrock.resources.agents import AgentsResource
from fondat.pagination import Page


async def test_list_aliases(mock_clients, config):
    """Test listing agent aliases with pagination support."""
    agent_client, _ = mock_clients
    agent_client.list_agent_aliases.return_value = {
        "agentAliasSummaries": [{"agentAliasId": "a1"}],
        "nextToken": "t",
    }
    page = await AgentsResource(config_agent=config, config_runtime=config)[
        "agent-1"
    ].aliases.get(max_results=3)
    assert isinstance(page, Page)
    agent_client.list_agent_aliases.assert_called_once_with(agentId="agent-1", maxResults=3)


async def test_get_alias(mock_clients, config):
    """Test retrieving a specific agent alias by ID."""
    agent_client, _ = mock_clients
    agent_client.get_agent_alias.return_value = {"agentAliasId": "a1"}
    res = await AgentsResource(config_agent=config, config_runtime=config)[
        "agent-1"
    ].aliases.get_alias("a1")
    assert res["agentAliasId"] == "a1"
    agent_client.get_agent_alias.assert_called_once_with(agentId="agent-1", agentAliasId="a1")


async def test_list_collaborators(mock_clients, config):
    """Test listing agent collaborators with pagination."""
    agent_client, _ = mock_clients
    agent_client.list_agent_collaborators.return_value = {
        "agentCollaboratorSummaries": [
            {
                "agentDescriptor": {
                    "aliasArn": "arn:aws:bedrock:us-east-2:123456789012:agent/agent-1/alias/a1"
                },
                "agentId": "agent-1",
                "agentVersion": "v1",
                "collaborationInstruction": "Test instruction",
                "collaboratorId": "c1",
                "collaboratorName": "Test Collaborator",
                "createdAt": "2024-01-01T00:00:00Z",
                "lastUpdatedAt": "2024-01-01T00:00:00Z",
                "relayConversationHistory": "TO_COLLABORATOR"
            }
        ],
        "nextToken": None,
    }
    page = await AgentsResource(config_agent=config, config_runtime=config)[
        "agent-1"
    ].collaborators.get(agentVersion="v1", max_results=10)
    assert isinstance(page, Page)
    assert len(page.items) == 1
    assert page.items[0]["collaboratorId"] == "c1"
    agent_client.list_agent_collaborators.assert_called_once_with(
        agentId="agent-1",
        agentVersion="v1",
        maxResults=10
    )


async def test_get_collaborator(mock_clients, config):
    """Test retrieving a specific collaborator by ID."""
    agent_client, _ = mock_clients
    agent_client.get_agent_collaborator.return_value = {
        "agentCollaborator": {
            "agentDescriptor": {
                "aliasArn": "arn:aws:bedrock:us-east-2:123456789012:agent/agent-1/alias/a1"
            },
            "agentId": "agent-1",
            "agentVersion": "v1",
            "clientToken": "token",
            "collaborationInstruction": "Test instruction",
            "collaboratorId": "c1",
            "collaboratorName": "Test Collaborator",
            "createdAt": "2024-01-01T00:00:00Z",
            "lastUpdatedAt": "2024-01-01T00:00:00Z",
            "relayConversationHistory": "TO_COLLABORATOR"
        }
    }
    res = await AgentsResource(config_agent=config, config_runtime=config)[
        "agent-1"
    ].collaborators.get_collaborator("c1", "v1")
    assert res["agentCollaborator"]["collaboratorId"] == "c1"
    agent_client.get_agent_collaborator.assert_called_once_with(
        agentId="agent-1",
        agentVersion="v1",
        collaboratorId="c1"
    )


async def test_list_prompts(mock_clients, config):
    """Test listing agent prompts with pagination."""
    agent_client, _ = mock_clients
    agent_client.list_prompts.return_value = {
        "promptSummaries": [{"promptId": "p1"}],
        "nextToken": "p",
    }
    page = await AgentsResource(config_agent=config, config_runtime=config)[
        "agent-1"
    ].prompts.get()
    assert isinstance(page, Page)
    agent_client.list_prompts.assert_called_once_with()


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
    res = await AgentsResource(config_agent=config, config_runtime=config)[
        "agent-1"
    ].prompts.get_prompt("p1")
    assert res["id"] == "p1"
    agent_client.get_prompt.assert_called_once_with(promptIdentifier="p1")


async def test_list_action_groups(mock_clients, config):
    """Test listing agent action groups with pagination."""
    agent_client, _ = mock_clients
    agent_client.list_agent_action_groups.return_value = {
        "actionGroupSummaries": [{"actionGroupId": "ag1"}],
        "nextToken": None,
    }
    page = await AgentsResource(config_agent=config, config_runtime=config)[
        "agent-1"
    ].action_groups.get(agentVersion="v1", max_results=2)
    assert isinstance(page, Page)
    agent_client.list_agent_action_groups.assert_called_once_with(
        agentId="agent-1", agentVersion="v1", maxResults=2
    )


async def test_get_action_group(mock_clients, config):
    """Test retrieving a specific action group by ID."""
    agent_client, _ = mock_clients
    agent_client.get_agent_action_group.return_value = {"actionGroupId": "ag1"}
    res = await AgentsResource(config_agent=config, config_runtime=config)[
        "agent-1"
    ].action_groups.get_action_group("ag1", agentVersion="v1")
    assert res["actionGroupId"] == "ag1"
    agent_client.get_agent_action_group.assert_called_once_with(
        agentId="agent-1", actionGroupId="ag1", agentVersion="v1"
    )
