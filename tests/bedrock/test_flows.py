"""Tests for bedrock flows functionality."""

from fondat.aws.bedrock.resources.agents import AgentsResource
from fondat.pagination import Page


async def test_flow_invoke_minimal_params(mock_clients, config):
    """Test flow invocation with minimal required parameters."""
    _, runtime_client = mock_clients
    runtime_client.invoke_flow.return_value = {"flow": "done"}

    res = (
        await AgentsResource(config_agent=config, config_runtime=config)["agent-1"]
        .flows["flow1"]
        .invoke(inputText="test", flowAliasIdentifier="alias1")
    )
    assert res == {"flow": "done"}
    runtime_client.invoke_flow.assert_called_once_with(
        flowIdentifier="flow1",
        flowAliasIdentifier="alias1",
        inputs=[{"nodeName": "input", "content": {"document": "test"}}],
        enableTrace=False,
    )


async def test_flow_invoke_optional_params(mock_clients, config):
    """Test flow invocation with optional parameters."""
    _, runtime_client = mock_clients
    runtime_client.invoke_flow.return_value = {"flow": "done"}

    res = (
        await AgentsResource(config_agent=config, config_runtime=config)["agent-1"]
        .flows["flow1"]
        .invoke(
            inputText="foo",
            flowAliasIdentifier="alias1",
            nodeName="start",
            nodeInputName="in",
            nodeOutputName="out",
            enableTrace=True,
            executionId="exec-1",
            modelPerformanceConfiguration={"threads": 2},
        )
    )
    assert res == {"flow": "done"}
    runtime_client.invoke_flow.assert_called_once_with(
        flowIdentifier="flow1",
        flowAliasIdentifier="alias1",
        inputs=[
            {
                "nodeName": "start",
                "content": {"document": "foo"},
                "nodeInputName": "in",
                "nodeOutputName": "out",
            }
        ],
        enableTrace=True,
        executionId="exec-1",
        modelPerformanceConfiguration={"performanceConfig": {"threads": 2}},
    )


async def test_list_flows(mock_clients, config):
    """Test listing flows with pagination support."""
    agent_client, _ = mock_clients
    agent_client.list_flows.return_value = {
        "flowSummaries": [{"flowIdentifier": "f1"}],
        "nextToken": "t",
    }
    page = await AgentsResource(config_agent=config, config_runtime=config)[
        "agent-1"
    ].flows.get(max_results=5)
    assert isinstance(page, Page)
    agent_client.list_flows.assert_called_once_with(maxResults=5)


async def test_get_flow(mock_clients, config):
    """Test retrieving a specific flow by ID."""
    agent_client, _ = mock_clients
    agent_client.get_flow.return_value = {"flowIdentifier": "f1"}
    res = await AgentsResource(config_agent=config, config_runtime=config)[
        "agent-1"
    ].flows.get_flow("f1")
    assert res["flowIdentifier"] == "f1"
    agent_client.get_flow.assert_called_once_with(flowIdentifier="f1")


async def test_list_flow_versions(mock_clients, config):
    """Test listing flow versions with pagination."""
    agent_client, _ = mock_clients
    agent_client.list_flow_versions.return_value = {
        "flowVersionSummaries": [{"flowVersion": "fv1"}],
        "nextToken": None,
    }
    page = await AgentsResource(config_agent=config, config_runtime=config)[
        "agent-1"
    ].flows.list_flow_versions("f1", max_results=1)
    assert isinstance(page, Page)
    agent_client.list_flow_versions.assert_called_once_with(flowIdentifier="f1", maxResults=1)


async def test_get_flow_version(mock_clients, config):
    """Test retrieving a specific flow version by ID."""
    agent_client, _ = mock_clients
    agent_client.get_flow_version.return_value = {"flowVersion": "fv1"}
    res = await AgentsResource(config_agent=config, config_runtime=config)[
        "agent-1"
    ].flows.get_flow_version("f1", "fv1")
    assert res["flowVersion"] == "fv1"
    agent_client.get_flow_version.assert_called_once_with(
        flowIdentifier="f1", flowVersion="fv1"
    )
