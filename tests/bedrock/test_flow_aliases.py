"""Tests for bedrock flow aliases functionality."""

from fondat.aws.bedrock.resources.agents import AgentsResource
from fondat.pagination import Page


async def test_list_flow_aliases(mock_clients, config):
    """Test listing flow aliases with pagination."""
    agent_client, _ = mock_clients
    agent_client.list_flow_aliases.return_value = {
        "flowAliasSummaries": [{"aliasIdentifier": "fa1"}],
        "nextToken": None,
    }
    page = await AgentsResource(config_agent=config, config_runtime=config)[
        "agent-1"
    ].flows.list_flow_aliases("f1", max_results=1)
    assert isinstance(page, Page)
    agent_client.list_flow_aliases.assert_called_once_with(flowIdentifier="f1", maxResults=1)


async def test_get_flow_alias(mock_clients, config):
    """Test retrieving a specific flow alias by ID."""
    agent_client, _ = mock_clients
    agent_client.get_flow_alias.return_value = {"aliasIdentifier": "fa1"}
    res = await AgentsResource(config_agent=config, config_runtime=config)[
        "agent-1"
    ].flows.get_flow_alias("f1", "fa1")
    assert res["aliasIdentifier"] == "fa1"
    agent_client.get_flow_alias.assert_called_once_with(
        flowIdentifier="f1", aliasIdentifier="fa1"
    )
