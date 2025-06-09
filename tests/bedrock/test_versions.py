from fondat.aws.bedrock.resources.agents import AgentsResource
from fondat.aws.bedrock.domain import AgentVersion

async def test_get_version(mock_clients, config):
    """Test getting version details."""
    agent_client, _ = mock_clients
    agent_client.get_agent_version.return_value = {
        "versionArn": "arn:aws:bedrock:us-east-1:123456789012:agent/a1/version/v1",
        "versionId": "v1",
        "version": "v1",
        "status": "ACTIVE",
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-01T00:00:00Z",
        "agentId": "a1",
        "agentName": "Test Agent",
        "agentStatus": "ACTIVE",
        "description": "Test version",
        "agentVersion": "v1"
    }

    res = await AgentsResource(config_agent=config)["a1"].versions["v1"].get()
    assert isinstance(res, AgentVersion)
    assert res.versionArn == "arn:aws:bedrock:us-east-1:123456789012:agent/a1/version/v1"
    assert res.versionId == "v1"
    assert res.version == "v1"
    assert res.status == "ACTIVE"
    assert res.agentId == "a1"
    assert res.agentName == "Test Agent"
    assert res.agentStatus == "ACTIVE"
    assert res.description == "Test version"
    assert res.agentVersion == "v1"
    agent_client.get_agent_version.assert_called_once_with(
        agentId="a1",
        agentVersion="v1"
    )


async def test_get_version_with_optional_fields(mock_clients, config):
    """Test getting version details with optional fields."""
    agent_client, _ = mock_clients
    agent_client.get_agent_version.return_value = {
        "versionArn": "arn:aws:bedrock:us-east-1:123456789012:agent/a1/version/v1",
        "versionId": "v1",
        "version": "v1",
        "status": "ACTIVE",
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-01T00:00:00Z",
        "agentId": "a1",
        "agentName": "Test Agent",
        "agentStatus": "ACTIVE",
        "description": "Test version",
        "customerEncryptionKeyArn": "arn:aws:kms:us-east-1:123456789012:key/k1",
        "executionRoleArn": "arn:aws:iam::123456789012:role/r1",
        "definition": {"key": "value"},
        "agentCollaboration": "ENABLED",
        "agentResourceRoleArn": "arn:aws:iam::123456789012:role/r2",
        "failureReasons": ["reason1", "reason2"],
        "foundationModel": "anthropic.claude-v2",
        "guardrailConfiguration": {"key": "value"},
        "idleSessionTtlInSeconds": 3600,
        "instruction": "Test instruction",
        "memoryConfiguration": {"key": "value"},
        "promptOverrideConfiguration": {"key": "value"},
        "recommendedActions": ["action1", "action2"],
        "agentVersion": "v1"
    }

    res = await AgentsResource(config_agent=config)["a1"].versions["v1"].get()
    assert isinstance(res, AgentVersion)
    assert res.versionArn == "arn:aws:bedrock:us-east-1:123456789012:agent/a1/version/v1"
    assert res.versionId == "v1"
    assert res.version == "v1"
    assert res.status == "ACTIVE"
    assert res.agentId == "a1"
    assert res.agentName == "Test Agent"
    assert res.agentStatus == "ACTIVE"
    assert res.description == "Test version"
    assert res.customerEncryptionKeyArn == "arn:aws:kms:us-east-1:123456789012:key/k1"
    assert res.executionRoleArn == "arn:aws:iam::123456789012:role/r1"
    assert res.definition == {"key": "value"}
    assert res.agentCollaboration == "ENABLED"
    assert res.agentResourceRoleArn == "arn:aws:iam::123456789012:role/r2"
    assert res.failureReasons == ["reason1", "reason2"]
    assert res.foundationModel == "anthropic.claude-v2"
    assert res.guardrailConfiguration == {"key": "value"}
    assert res.idleSessionTtlInSeconds == 3600
    assert res.instruction == "Test instruction"
    assert res.memoryConfiguration == {"key": "value"}
    assert res.promptOverrideConfiguration == {"key": "value"}
    assert res.recommendedActions == ["action1", "action2"]
    assert res.agentVersion == "v1"
    agent_client.get_agent_version.assert_called_once_with(
        agentId="a1",
        agentVersion="v1"
    ) 