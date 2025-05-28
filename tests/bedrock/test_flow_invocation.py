"""Tests for bedrock flow invocation."""

from fondat.aws.bedrock.resources.agents import AgentsResource


async def test_flow_invoke_minimal_params(mock_clients, config):
    """Test flow invocation with minimal required parameters."""
    _, runtime_client = mock_clients
    runtime_client.invoke_flow.return_value = {"flow": "done"}

    res = (
        await AgentsResource(config_agent=config, config_runtime=config)["agent-1"]
        .flows["flow1"]
        .invoke(input_content="test", flowAliasIdentifier="alias1")
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
