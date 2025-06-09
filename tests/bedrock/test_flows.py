"""Tests for bedrock flows functionality."""

from fondat.aws.bedrock.resources.agents import AgentsResource
from fondat.pagination import Page
import json
from fondat.aws.bedrock.resources.generic_resources import GenericVersionResource


async def test_flow_invoke_minimal_params(mock_clients, config):
    """Test flow invocation with minimal required parameters."""
    _, runtime_client = mock_clients
    runtime_client.invoke_flow.return_value = {
        "executionId": "exec-1",
        "responseStream": "test response"
    }

    res = (
        await AgentsResource(config_agent=config, config_runtime=config)["agent-1"]
        .flows["flow1"]
        .invoke(input_content="test", flowAliasIdentifier="alias1")
    )
    assert res.executionId == "exec-1"
    assert res.responseStream == "test response"
    runtime_client.invoke_flow.assert_called_once_with(
        flowIdentifier="flow1",
        flowAliasIdentifier="alias1",
        inputs=[{
            "nodeName": "input",
            "content": {
                "document": "test"
            }
        }],
        enableTrace=False
    )


async def test_flow_invoke_optional_params(mock_clients, config):
    """Test flow invocation with optional parameters."""
    _, runtime_client = mock_clients
    runtime_client.invoke_flow.return_value = {
        "executionId": "exec-1",
        "responseStream": "test response"
    }

    res = (
        await AgentsResource(config_agent=config, config_runtime=config)["agent-1"]
        .flows["flow1"]
        .invoke(
            input_content="foo",
            flowAliasIdentifier="alias1",
            nodeName="start",
            nodeInputName="in",
            nodeOutputName="out",
            enableTrace=True,
            executionId="exec-1",
            modelPerformanceConfiguration={"threads": 2},
        )
    )
    assert res.executionId == "exec-1"
    assert res.responseStream == "test response"
    runtime_client.invoke_flow.assert_called_once_with(
        flowIdentifier="flow1",
        flowAliasIdentifier="alias1",
        inputs=[{
            "nodeName": "start",
            "nodeInputName": "in",
            "nodeOutputName": "out",
            "content": {
                "document": "foo"
            }
        }],
        enableTrace=True,
        executionId="exec-1",
        modelPerformanceConfiguration={
            "performanceConfig": {"threads": 2}
        }
    )


async def test_list_flows(mock_clients, config):
    """Test listing flows with pagination support."""
    agent_client, _ = mock_clients
    agent_client.list_flows.return_value = {
        "flowSummaries": [{
            "id": "f1",
            "name": "Test Flow",
            "status": "ACTIVE",
            "createdAt": "2024-03-20T00:00:00Z",
            "description": "Test flow description"
        }],
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
    agent_client.get_flow.return_value = {
        "flowId": "f1",
        "flowArn": "arn:aws:bedrock:us-east-2:123456789012:flow/f1",
        "flowName": "Test Flow",
        "status": "ACTIVE",
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-01T00:00:00Z",
        "definition": {},
        "version": "1"
    }
    res = await AgentsResource(config_agent=config, config_runtime=config)[
        "agent-1"
    ].flows["f1"].get()
    assert res.flowId == "f1"
    assert res.flowName == "Test Flow"
    assert res.status == "ACTIVE"
    agent_client.get_flow.assert_called_once_with(flowIdentifier="f1")


async def test_list_flow_versions_with_generic(mock_clients, config):
    """Test listing flow versions using the generic class."""
    agent_client, _ = mock_clients
    agent_client.list_flow_versions.return_value = {
        "flowVersionSummaries": [{
            "flowVersion": "fv1",
            "versionName": "Flow Version 1",
            "createdAt": "2024-03-20T10:00:00Z"
        }],
        "nextToken": "t",
    }

    # Create a GenericVersionResource instance for flows
    versions = GenericVersionResource(
        "f1",  # flow identifier
        id_field="flowIdentifier",
        list_method="list_flow_versions",
        get_method="get_flow_version",
        items_key="flowVersionSummaries",
        config=config
    )

    page = await versions.get(max_results=1)
    assert isinstance(page, Page)
    assert len(page.items) == 1
    assert page.items[0].version_id == "fv1"
    agent_client.list_flow_versions.assert_called_once_with(
        flowIdentifier="f1", maxResults=1
    )


async def test_get_flow_version_with_generic(mock_clients, config):
    """Test retrieving a specific flow version using the generic class."""
    agent_client, _ = mock_clients
    agent_client.get_flow_version.return_value = {
        "versionArn": "arn:aws:bedrock:us-east-1:123456789012:flow/f1/version/fv1",
        "versionId": "fv1",
        "version": "1",
        "status": "ACTIVE",
        "createdAt": "2024-03-20T10:00:00Z",
        "updatedAt": "2024-03-20T10:00:00Z",
        "flowVersion": "fv1",
        "flowId": "f1",
        "flowName": "Test Flow",
        "definition": {}
    }

    # Create a GenericVersionResource instance for flows
    versions = GenericVersionResource(
        "f1",  # flow identifier
        id_field="flowIdentifier",
        list_method="list_flow_versions",
        get_method="get_flow_version",
        items_key="flowVersionSummaries",
        config=config
    )

    result = await versions["fv1"].get()
    assert result.versionArn == "arn:aws:bedrock:us-east-1:123456789012:flow/f1/version/fv1"
    assert result.versionId == "fv1"
    assert result.version == "1"
    assert result.status == "ACTIVE"
    assert result.flowVersion == "fv1"
    assert result.flowId == "f1"
    assert result.flowName == "Test Flow"
    assert result.definition == {}
    agent_client.get_flow_version.assert_called_once_with(
        flowIdentifier="f1",
        flowVersion="fv1"
    )


async def test_flow_invoke_complex_json_input(mock_clients, config):
    """Test flow invocation with complex JSON input containing various data types."""
    _, runtime_client = mock_clients
    runtime_client.invoke_flow.return_value = {
        "executionId": "exec-1",
        "responseStream": "test response"
    }

    complex_input = {
        "text": "Hello World",
        "number": 42,
        "float": 3.14159,
        "boolean": True,
        "null_value": None,
        "array": [1, "two", False, None],
        "nested": {
            "key": "value",
            "numbers": [1, 2, 3],
            "empty": {}
        }
    }

    res = (
        await AgentsResource(config_agent=config, config_runtime=config)["agent-1"]
        .flows["flow1"]
        .invoke(
            input_content=complex_input,
            flowAliasIdentifier="alias1",
            nodeName="complex_input",
            enableTrace=True
        )
    )
    assert res.executionId == "exec-1"
    assert res.responseStream == "test response"
    runtime_client.invoke_flow.assert_called_once_with(
        flowIdentifier="flow1",
        flowAliasIdentifier="alias1",
        inputs=[{
            "nodeName": "complex_input",
            "content": {
                "document": json.dumps(complex_input)
            }
        }],
        enableTrace=True
    )


async def test_invoke_flow(mock_clients, config):
    """Test invoking a flow with input content."""
    _, runtime_client = mock_clients
    runtime_client.invoke_flow.return_value = {
        "executionId": "e1",
        "responseStream": "test response"
    }
    res = await AgentsResource(config_agent=config, config_runtime=config)[
        "agent-1"
    ].flows["f1"].invoke(
        input_content="test input",
        flowAliasIdentifier="fa1",
        enableTrace=True
    )
    assert res.executionId == "e1"
    assert res.responseStream == "test response"
    runtime_client.invoke_flow.assert_called_once_with(
        flowIdentifier="f1",
        flowAliasIdentifier="fa1",
        inputs=[{
            "nodeName": "input",
            "content": {
                "document": "test input"
            }
        }],
        enableTrace=True
    )
