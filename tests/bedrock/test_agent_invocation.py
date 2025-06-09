"""Tests for bedrock agent invocation."""

from fondat.aws.bedrock.resources.agents import AgentsResource


async def test_invoke_agent(mock_clients, config):
    """Test invoking an agent with input text and session tracking."""
    _, runtime_client = mock_clients
    runtime_client.invoke_agent.return_value = {
        "completion": "test completion",
        "sessionId": "s1",
        "contentType": "text/plain"
    }
    res = await AgentsResource(config_agent=config, config_runtime=config)["agent-1"].invoke(
        inputText="hi", sessionId="s1", agentAliasId="alias-1", enableTrace=True
    )
    assert res.completion == "test completion"
    assert res.sessionId == "s1"
    assert res.contentType == "text/plain"
    runtime_client.invoke_agent.assert_called_once_with(
        agentId="agent-1",
        inputText="hi",
        sessionId="s1",
        agentAliasId="alias-1",
        enableTrace=True,
    )



async def test_invoke_agent_edge_cases(mock_clients, config):
    """Test agent invocation with various input edge cases."""
    _, runtime_client = mock_clients
    runtime_client.invoke_agent.return_value = {
        "completion": "test completion",
        "sessionId": "s1",
        "contentType": "text/plain"
    }

    # Test with empty input
    res = await AgentsResource(config_agent=config, config_runtime=config)["agent-1"].invoke(
        inputText="", sessionId="s1", agentAliasId="alias-1"
    )
    assert res.completion == "test completion"
    assert res.sessionId == "s1"
    assert res.contentType == "text/plain"

    # Test with very long input
    long_input = "x" * 10000
    await AgentsResource(config_agent=config, config_runtime=config)["agent-1"].invoke(
        inputText=long_input, sessionId="s1", agentAliasId="alias-1"
    )

    # Test with special characters
    await AgentsResource(config_agent=config, config_runtime=config)["agent-1"].invoke(
        inputText="!@#$%^&*()", sessionId="s1", agentAliasId="alias-1"
    )
