"""Tests for bedrock agent invocation."""

from fondat.aws.bedrock.resources.agents import AgentsResource


async def test_invoke_agent(mock_clients, config):
    """Test invoking an agent with input text and session tracking."""
    _, runtime_client = mock_clients
    runtime_client.invoke_agent.return_value = {"result": "ok"}
    res = await AgentsResource(config_agent=config, config_runtime=config)["agent-1"].invoke(
        inputText="hi", sessionId="s1", agentAliasId="alias-1", enableTrace=True
    )
    assert res["result"] == "ok"
    runtime_client.invoke_agent.assert_called_once_with(
        agentId="agent-1", inputText="hi", sessionId="s1", agentAliasId="alias-1", enableTrace=True
    )


async def test_invoke_inline_agent(mock_clients, config):
    """Test invoking an inline agent with custom instruction and model."""
    _, runtime_client = mock_clients
    runtime_client.invoke_inline_agent.return_value = {"inline": True}
    res = await AgentsResource(config_agent=config, config_runtime=config)[
        "agent-1"
    ].invoke_inline_agent(inputText="x", instruction="i", foundationModel="m", sessionId="s")
    assert res["inline"] is True
    runtime_client.invoke_inline_agent.assert_called_once_with(
        agentId="agent-1", inputText="x", instruction="i", foundationModel="m", sessionId="s"
    )


async def test_invoke_agent_edge_cases(mock_clients, config):
    """Test agent invocation with various input edge cases."""
    _, runtime_client = mock_clients
    runtime_client.invoke_agent.return_value = {"result": "ok"}

    # Test with empty input
    await AgentsResource(config_agent=config, config_runtime=config)["agent-1"].invoke(
        inputText="", sessionId="s1", agentAliasId="alias-1"
    )

    # Test with very long input
    long_input = "x" * 10000
    await AgentsResource(config_agent=config, config_runtime=config)["agent-1"].invoke(
        inputText=long_input, sessionId="s1", agentAliasId="alias-1"
    )

    # Test with special characters
    await AgentsResource(config_agent=config, config_runtime=config)["agent-1"].invoke(
        inputText="!@#$%^&*()", sessionId="s1", agentAliasId="alias-1"
    )
