"""Tests for bedrock aliases and collaborators functionality."""

from fondat.aws.bedrock.resources.agents import AgentsResource
from fondat.aws.bedrock.resources.prompts import PromptsResource
from fondat.aws.bedrock.domain import AgentAlias
from fondat.pagination import Page


async def test_list_agent_aliases_with_generic(mock_clients, config):
    """Test listing agent aliases using the generic resource."""
    agent_client, _ = mock_clients
    agent_client.list_agent_aliases.return_value = {
        "agentAliasSummaries": [{
            "aliasId": "a1",
            "aliasName": "Alias 1",
            "createdAt": "2024-03-20T10:00:00Z"
        }],
        "nextToken": "t",
    }

    page = await AgentsResource(config_agent=config, config_runtime=config)[
        "agent-1"
    ].aliases.get(max_results=1)

    assert isinstance(page, Page)
    agent_client.list_agent_aliases.assert_called_once_with(
        agentId="agent-1", maxResults=1
    )


async def test_get_agent_alias_with_generic(mock_clients, config):
    """Test retrieving a specific agent alias using the generic resource."""
    agent_client, _ = mock_clients
    agent_client.get_agent_alias.return_value = {
        "agent_alias_arn": "arn:aws:bedrock:us-east-1:123456789012:agent/a1/alias/a1",
        "agent_alias_id": "a1",
        "agent_alias_name": "Test Alias",
        "agent_alias_status": "ACTIVE",
        "agent_id": "agent-1",
        "created_at": "2024-03-20T10:00:00Z",
        "updated_at": "2024-03-20T10:00:00Z"
    }

    result = await AgentsResource(config_agent=config, config_runtime=config)[
        "agent-1"
    ].aliases["a1"].get()

    assert isinstance(result, AgentAlias)
    assert result.agent_alias_arn == "arn:aws:bedrock:us-east-1:123456789012:agent/a1/alias/a1"
    assert result.agent_alias_id == "a1"
    assert result.agent_alias_name == "Test Alias"
    assert result.agent_alias_status == "ACTIVE"
    assert result.agent_id == "agent-1"
    assert result.created_at == "2024-03-20T10:00:00Z"
    assert result.updated_at == "2024-03-20T10:00:00Z"

    agent_client.get_agent_alias.assert_called_once_with(
        agentId="agent-1",
        agentAliasId="a1"
    )


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
                "collaboratorType": "USER",
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
    assert page.items[0].collaborator_id == "c1"
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
    ].collaborators["c1"].get(agentVersion="v1")
    assert res.collaboratorId == "c1"
    agent_client.get_agent_collaborator.assert_called_once_with(
        agentId="agent-1",
        agentVersion="v1",
        collaboratorId="c1"
    )


async def test_list_prompts(mock_clients, config):
    """Test listing agent prompts with pagination."""
    agent_client, _ = mock_clients
    agent_client.list_prompts.return_value = {
        "promptSummaries": [{
            "promptId": "p1",
            "promptName": "Prompt 1",
            "createdAt": "2024-03-20T10:00:00Z"
        }],
        "nextToken": "p",
    }
    page = await PromptsResource(config_agent=config).get()
    assert isinstance(page, Page)
    agent_client.list_prompts.assert_called_once_with()


async def test_get_prompt(mock_clients, config):
    """Test retrieving a specific prompt by ID."""
    agent_client, _ = mock_clients
    agent_client.get_prompt.return_value = {
        "promptArn": "arn:aws:bedrock:us-east-2:123456789012:prompt/p1",
        "promptId": "p1",
        "promptName": "Test",
        "version": "v1",
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-01T00:00:00Z",
        "variants": [],
        "description": "Test prompt"
    }
    res = await PromptsResource(config_agent=config)["p1"].get()
    assert res.promptArn == "arn:aws:bedrock:us-east-2:123456789012:prompt/p1"
    assert res.promptId == "p1"
    assert res.promptName == "Test"
    assert res.version == "v1"
    assert res.description == "Test prompt"
    agent_client.get_prompt.assert_called_once_with(promptIdentifier="p1")


async def test_list_action_groups(mock_clients, config):
    """Test listing agent action groups with pagination."""
    agent_client, _ = mock_clients
    agent_client.list_agent_action_groups.return_value = {
        "actionGroupSummaries": [{
            "actionGroupId": "ag1",
            "actionGroupName": "Action Group 1"
        }],
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
    agent_client.get_agent_action_group.return_value = {
        "agentActionGroup": {
            "actionGroupId": "ag1",
            "actionGroupName": "Test Action Group",
            "actionGroupState": "ENABLED",
            "agentId": "agent-1",
            "agentVersion": "v1",
            "createdAt": "2024-01-01T00:00:00Z",
            "updatedAt": "2024-01-01T00:00:00Z",
            "description": "Test description",
            "actionGroupExecutor": {
                "customControl": "RETURN_CONTROL",
                "lambda": "arn:aws:lambda:us-east-2:123456789012:function:test-function"
            },
            "apiSchema": {
                "payload": "test payload"
            },
            "functionSchema": {
                "functions": [
                    {
                        "name": "testFunction",
                        "description": "Test function",
                        "parameters": {
                            "param1": {
                                "description": "Test parameter",
                                "required": True,
                                "type": "string"
                            }
                        },
                        "requireConfirmation": "ENABLED"
                    }
                ]
            }
        }
    }
    res = await AgentsResource(config_agent=config, config_runtime=config)["agent-1"].action_groups["ag1"].get(agentVersion="v1")
    assert res.actionGroupId == "ag1"
    assert res.actionGroupName == "Test Action Group"
    assert res.actionGroupState == "ENABLED"
    assert res.agentId == "agent-1"
    assert res.agentVersion == "v1"
    assert res.createdAt == "2024-01-01T00:00:00Z"
    assert res.updatedAt == "2024-01-01T00:00:00Z"
    assert res.description == "Test description"
    assert res.actionGroupExecutor.customControl == "RETURN_CONTROL"
    assert res.actionGroupExecutor.lambda_ == "arn:aws:lambda:us-east-2:123456789012:function:test-function"
    assert res.apiSchema.payload == "test payload"
    assert len(res.functionSchema.functions) == 1
    assert res.functionSchema.functions[0].name == "testFunction"
    assert res.functionSchema.functions[0].description == "Test function"
    assert res.functionSchema.functions[0].parameters["param1"].description == "Test parameter"
    assert res.functionSchema.functions[0].parameters["param1"].required is True
    assert res.functionSchema.functions[0].parameters["param1"].type == "string"
    assert res.functionSchema.functions[0].requireConfirmation == "ENABLED"

    agent_client.get_agent_action_group.assert_called_once_with(
        agentId="agent-1",
        actionGroupId="ag1",
        agentVersion="v1"
    )
