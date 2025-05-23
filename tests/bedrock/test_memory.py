"""Tests for bedrock memory functionality."""

from fondat.aws.bedrock.resources.agents import AgentsResource


async def test_get_memory(mock_clients, config):
    """Test retrieving agent memory with pagination."""
    _, runtime_client = mock_clients
    runtime_client.get_agent_memory.return_value = {
        "memoryContents": [
            {
                "sessionSummary": {
                    "memoryId": "mid",
                    "sessionExpiryTime": "2024-01-01T00:00:00Z",
                    "sessionId": "sid",
                    "sessionStartTime": "2024-01-01T00:00:00Z",
                    "summaryText": "Test summary"
                }
            }
        ],
        "nextToken": "next_token"
    }
    res = await AgentsResource(config_agent=config, config_runtime=config)[
        "agent-1"
    ].memory.get(
        memoryId="mid",
        agentAliasId="alias-1",
        memoryType="SESSION_SUMMARY",
        max_items=10,
        cursor="prev_token"
    )
    assert len(res["memoryContents"]) == 1
    assert res["memoryContents"][0]["sessionSummary"]["memoryId"] == "mid"
    assert res["memoryContents"][0]["sessionSummary"]["sessionId"] == "sid"
    assert res["memoryContents"][0]["sessionSummary"]["summaryText"] == "Test summary"
    assert res["nextToken"] == "next_token"
    runtime_client.get_agent_memory.assert_called_once_with(
        agentId="agent-1",
        memoryId="mid",
        agentAliasId="alias-1",
        memoryType="SESSION_SUMMARY",
        maxItems=10,
        nextToken="prev_token"
    )


async def test_delete_memory(mock_clients, config):
    """Test deleting agent memory."""
    _, runtime_client = mock_clients
    await AgentsResource(config_agent=config, config_runtime=config)["agent-1"].memory.delete(
        memoryId="mid",
        agentAliasId="alias-1",
        sessionId="sid"
    )
    runtime_client.delete_agent_memory.assert_called_once_with(
        agentId="agent-1",
        memoryId="mid",
        agentAliasId="alias-1",
        sessionId="sid"
    )
