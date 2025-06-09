"""Tests for bedrock flow aliases functionality."""

from fondat.aws.bedrock.resources.agents import AgentsResource
from fondat.aws.bedrock.resources.generic_resources import GenericAliasResource
from fondat.aws.bedrock.domain import FlowAlias
from fondat.pagination import Page


async def test_list_flow_aliases_with_generic(mock_clients, config):
    """Test listing flow aliases using the generic resource."""
    agent_client, _ = mock_clients
    agent_client.list_flow_aliases.return_value = {
        "flowAliasSummaries": [{
            "aliasIdentifier": "fa1",
            "aliasName": "Flow Alias 1",
            "createdAt": "2024-03-20T10:00:00Z"
        }],
        "nextToken": "t",
    }

    # Create a GenericAliasResource instance for flows
    aliases = GenericAliasResource(
        "f1",  # flow identifier
        id_field="flowIdentifier",
        list_method="list_flow_aliases",
        get_method="get_flow_alias",
        items_key="flowAliasSummaries",
        config=config
    )

    page = await aliases.get(max_results=1)
    assert isinstance(page, Page)
    assert len(page.items) == 1
    assert page.items[0].alias_id == "fa1"
    agent_client.list_flow_aliases.assert_called_once_with(
        flowIdentifier="f1", maxResults=1
    )


async def test_get_flow_alias(mock_clients, config):
    """Test retrieving a specific flow alias by ID."""
    agent_client, _ = mock_clients
    agent_client.get_flow_alias.return_value = {
        "arn": "arn:aws:bedrock:us-east-1:123456789012:flow/f1/alias/fa1",
        "flow_alias_id": "fa1",
        "flow_alias_name": "Flow Alias 1",
        "flow_id": "f1",
        "created_at": "2024-03-20T10:00:00Z",
        "updated_at": "2024-03-20T10:00:00Z"
    }

    # Create a GenericAliasResource instance for flows
    aliases = GenericAliasResource(
        "f1",  # flow identifier
        id_field="flowIdentifier",
        list_method="list_flow_aliases",
        get_method="get_flow_alias",
        items_key="flowAliasSummaries",
        config=config
    )

    res = await aliases["fa1"].get()

    assert isinstance(res, FlowAlias)
    assert res.arn == "arn:aws:bedrock:us-east-1:123456789012:flow/f1/alias/fa1"
    assert res.flow_alias_id == "fa1"
    assert res.flow_alias_name == "Flow Alias 1"
    assert res.flow_id == "f1"
    assert res.created_at == "2024-03-20T10:00:00Z"
    assert res.updated_at == "2024-03-20T10:00:00Z"

    agent_client.get_flow_alias.assert_called_once_with(
        flowIdentifier="f1",
        aliasIdentifier="fa1"
    )
