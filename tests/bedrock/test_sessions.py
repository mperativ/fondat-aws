"""Tests for session management."""

import pytest
from fondat.aws.bedrock import AgentsResource


@pytest.mark.asyncio
async def test_create_session(mock_clients, config):
    """Test creating a new session."""
    _, runtime_client = mock_clients
    runtime_client.create_session.return_value = {
        "sessionId": "sid",
        "sessionArn": "arn:aws:bedrock:us-east-2:123456789012:session/sid",
        "createdAt": "2024-01-01T00:00:00Z",
        "lastUpdatedAt": "2024-01-01T00:00:00Z",
        "sessionStatus": "ACTIVE",
        "sessionMetadata": {"k": "v"},
        "encryptionKeyArn": "arn:aws:kms:us-east-2:123456789012:key/abcd1234"
    }
    res = await AgentsResource(config_agent=config, config_runtime=config)["agent-1"].sessions.create(
        encryptionKeyArn="arn:aws:kms:us-east-2:123456789012:key/abcd1234",
        sessionMetadata={"k": "v"},
        tags={"tag1": "value1"}
    )
    assert res.sessionId == "sid"
    assert res.sessionArn == "arn:aws:bedrock:us-east-2:123456789012:session/sid"
    assert res.createdAt == "2024-01-01T00:00:00Z"
    assert res.lastUpdatedAt == "2024-01-01T00:00:00Z"
    assert res.sessionStatus == "ACTIVE"
    assert res.sessionMetadata == {"k": "v"}
    assert res.encryptionKeyArn == "arn:aws:kms:us-east-2:123456789012:key/abcd1234"

    runtime_client.create_session.assert_called_once_with(
        encryptionKeyArn="arn:aws:kms:us-east-2:123456789012:key/abcd1234",
        sessionMetadata={"k": "v"},
        tags={"tag1": "value1"}
    )


@pytest.mark.asyncio
async def test_get_session(mock_clients, config):
    """Test retrieving session details by ID."""
    _, runtime_client = mock_clients
    runtime_client.get_session.return_value = {
        "sessionId": "sid",
        "sessionArn": "arn:aws:bedrock:us-east-2:123456789012:session/sid",
        "createdAt": "2024-01-01T00:00:00Z",
        "lastUpdatedAt": "2024-01-01T00:00:00Z",
        "sessionStatus": "ACTIVE"
    }
    res = await AgentsResource(config_agent=config, config_runtime=config)["agent-1"].sessions["sid"].get()
    assert res.sessionId == "sid"
    assert res.sessionArn == "arn:aws:bedrock:us-east-2:123456789012:session/sid"
    assert res.createdAt == "2024-01-01T00:00:00Z"
    assert res.lastUpdatedAt == "2024-01-01T00:00:00Z"
    assert res.sessionStatus == "ACTIVE"

    runtime_client.get_session.assert_called_once_with(sessionIdentifier="sid")


@pytest.mark.asyncio
async def test_delete_session(mock_clients, config):
    """Test deleting a session by ID."""
    _, runtime_client = mock_clients
    await AgentsResource(config_agent=config, config_runtime=config)["agent-1"].sessions["sid"].delete()
    runtime_client.delete_session.assert_called_once_with(sessionIdentifier="sid")


@pytest.mark.asyncio
async def test_end_session(mock_clients, config):
    """Test ending an active session."""
    _, runtime_client = mock_clients
    runtime_client.end_session.return_value = {
        "sessionId": "sid",
        "sessionArn": "arn:aws:bedrock:us-east-2:123456789012:session/sid",
        "createdAt": "2024-01-01T00:00:00Z",
        "lastUpdatedAt": "2024-01-01T00:00:00Z",
        "sessionStatus": "ENDED"
    }
    res = await AgentsResource(config_agent=config, config_runtime=config)["agent-1"].sessions["sid"].end()
    assert res.sessionId == "sid"
    assert res.sessionArn == "arn:aws:bedrock:us-east-2:123456789012:session/sid"
    assert res.createdAt == "2024-01-01T00:00:00Z"
    assert res.lastUpdatedAt == "2024-01-01T00:00:00Z"
    assert res.sessionStatus == "ENDED"

    runtime_client.end_session.assert_called_once_with(sessionIdentifier="sid")


@pytest.mark.asyncio
async def test_update_session(mock_clients, config):
    """Test updating session metadata."""
    _, runtime_client = mock_clients
    runtime_client.update_session.return_value = {
        "sessionId": "sid",
        "sessionArn": "arn:aws:bedrock:us-east-2:123456789012:session/sid",
        "createdAt": "2024-01-01T00:00:00Z",
        "lastUpdatedAt": "2024-01-01T00:00:00Z",
        "sessionStatus": "ACTIVE"
    }
    res = await AgentsResource(config_agent=config, config_runtime=config)["agent-1"].sessions["sid"].update(
        sessionMetadata={"k": "v"}
    )
    assert res.sessionId == "sid"
    assert res.sessionArn == "arn:aws:bedrock:us-east-2:123456789012:session/sid"
    assert res.createdAt == "2024-01-01T00:00:00Z"
    assert res.lastUpdatedAt == "2024-01-01T00:00:00Z"
    assert res.sessionStatus == "ACTIVE"

    runtime_client.update_session.assert_called_once_with(
        sessionIdentifier="sid",
        sessionMetadata={"k": "v"}
    )


@pytest.mark.asyncio
async def test_create_invocation(mock_clients, config):
    """Test creating a new invocation within a session."""
    _, runtime_client = mock_clients
    runtime_client.create_invocation.return_value = {
        "sessionId": "sid",
        "invocationId": "iid",
        "createdAt": "2024-01-01T00:00:00Z"
    }
    res = await AgentsResource(config_agent=config, config_runtime=config)["agent-1"].sessions["sid"].invocations["iid"].create(
        description="Test invocation"
    )
    assert res.sessionId == "sid"
    assert res.invocationId == "iid"
    assert res.createdAt == "2024-01-01T00:00:00Z"

    runtime_client.create_invocation.assert_called_once_with(
        sessionIdentifier="sid",
        invocationId="iid",
        description="Test invocation"
    )


@pytest.mark.asyncio
async def test_put_step(mock_clients, config):
    """Test adding a step to an invocation."""
    _, runtime_client = mock_clients
    runtime_client.put_invocation_step.return_value = {"invocationStepId": "stp"}
    from datetime import datetime

    res = await AgentsResource(config_agent=config, config_runtime=config)["agent-1"].sessions["sid"].invocations["iid"].put_step(
        payload={
            "contentBlocks": [
                {
                    "text": "Hello, world!"
                }
            ]
        },
        invocationStepTime=datetime(2024, 1, 1),
        invocationStepId="stp"
    )
    assert res["invocationStepId"] == "stp"
    runtime_client.put_invocation_step.assert_called_once_with(
        sessionIdentifier="sid",
        invocationIdentifier="iid",
        payload={
            "contentBlocks": [
                {
                    "text": "Hello, world!"
                }
            ]
        },
        invocationStepTime=datetime(2024, 1, 1),
        invocationStepId="stp"
    )


@pytest.mark.asyncio
async def test_get_step(mock_clients, config):
    """Test retrieving invocation step details."""
    _, runtime_client = mock_clients
    runtime_client.get_invocation_step.return_value = {
        "invocationStep": {
            "invocationId": "iid",
            "invocationStepId": "step1",
            "invocationStepTime": "2024-01-01T00:00:00Z",
            "payload": {
                "contentBlocks": [
                    {
                        "text": "Hello, world!"
                    },
                    {
                        "image": {
                            "format": "png",
                            "source": {
                                "s3Location": {
                                    "uri": "s3://bucket/image.png"
                                }
                            }
                        }
                    }
                ]
            },
            "sessionId": "sid"
        }
    }
    res = await AgentsResource(config_agent=config, config_runtime=config)["agent-1"].sessions["sid"].invocations["iid"].get_step("step1")
    assert res.invocationId == "iid"
    assert res.invocationStepId == "step1"
    assert res.invocationStepTime == "2024-01-01T00:00:00Z"
    assert res.sessionId == "sid"
    assert len(res.payload.contentBlocks) == 2
    assert res.payload.contentBlocks[0].text == "Hello, world!"
    assert res.payload.contentBlocks[1].image.format == "png"
    assert res.payload.contentBlocks[1].image.source.s3Location["uri"] == "s3://bucket/image.png"

    runtime_client.get_invocation_step.assert_called_once_with(
        sessionIdentifier="sid",
        invocationIdentifier="iid",
        invocationStepId="step1"
    )


@pytest.mark.asyncio
async def test_list_steps(mock_clients, config):
    """Test listing all steps in an invocation with pagination."""
    _, runtime_client = mock_clients
    runtime_client.list_invocation_steps.return_value = {
        "invocationStepSummaries": [
            {
                "invocationId": "iid",
                "invocationStepId": "stp1",
                "invocationStepTime": "2024-01-01T00:00:00Z",
                "sessionId": "sid"
            }
        ],
        "nextToken": "next_token"
    }
    page = await AgentsResource(config_agent=config, config_runtime=config)["agent-1"].sessions["sid"].invocations["iid"].get_steps(
        max_results=10,
        cursor="prev_token".encode()
    )
    assert len(page.items) == 1
    assert page.items[0]["invocationStepId"] == "stp1"
    assert page.cursor == "next_token".encode()
    runtime_client.list_invocation_steps.assert_called_once_with(
        sessionIdentifier="sid",
        invocationIdentifier="iid",
        maxResults=10,
        nextToken="prev_token"
    )


@pytest.mark.asyncio
async def test_list_invocations(mock_clients, config):
    """Test listing all invocations in a session with pagination."""
    _, runtime_client = mock_clients
    runtime_client.list_invocations.return_value = {
        "invocationSummaries": [
            {
                "createdAt": "2024-01-01T00:00:00Z",
                "invocationId": "iid",
                "sessionId": "sid",
                "status": "COMPLETED",
                "inputText": "Test input"
            }
        ],
        "nextToken": "next_token"
    }
    page = await AgentsResource(config_agent=config, config_runtime=config)["agent-1"].sessions["sid"].invocations.get(
        max_results=10,
        cursor="prev_token".encode()
    )
    assert len(page.items) == 1
    assert page.items[0].invocation_id == "iid"
    assert page.cursor == "next_token".encode()
    runtime_client.list_invocations.assert_called_once_with(
        sessionIdentifier="sid",
        maxResults=10,
        nextToken="prev_token"
    )


@pytest.mark.asyncio
async def test_get_invocation_step(mock_clients, config):
    """Test retrieving a specific step from an invocation."""
    _, runtime_client = mock_clients
    runtime_client.get_invocation_step.return_value = {
        "invocationStep": {
            "invocationId": "iid",
            "invocationStepId": "stp",
            "invocationStepTime": "2024-01-01T00:00:00Z",
            "payload": {
                "contentBlocks": [
                    {
                        "text": "Hello, world!"
                    }
                ]
            },
            "sessionId": "sid"
        }
    }
    res = await AgentsResource(config_agent=config, config_runtime=config)["agent-1"].sessions["sid"].invocations["iid"].get_step(
        invocationStepId="stp"
    )
    assert res.invocationId == "iid"
    assert res.invocationStepId == "stp"
    assert res.invocationStepTime == "2024-01-01T00:00:00Z"
    assert res.sessionId == "sid"
    assert len(res.payload.contentBlocks) == 1
    assert res.payload.contentBlocks[0].text == "Hello, world!"

    runtime_client.get_invocation_step.assert_called_once_with(
        sessionIdentifier="sid",
        invocationIdentifier="iid",
        invocationStepId="stp"
    )


@pytest.mark.asyncio
async def test_list_invocation_steps(mock_clients, config):
    """Test listing all steps in an invocation with pagination."""
    _, runtime_client = mock_clients
    runtime_client.list_invocation_steps.return_value = {
        "invocationStepSummaries": [
            {
                "invocationId": "iid",
                "invocationStepId": "stp1",
                "invocationStepTime": "2024-01-01T00:00:00Z",
                "sessionId": "sid"
            }
        ],
        "nextToken": "next_token"
    }
    page = await AgentsResource(config_agent=config, config_runtime=config)["agent-1"].sessions["sid"].invocations["iid"].get_steps(
        max_results=10,
        cursor="prev_token".encode()
    )
    assert len(page.items) == 1
    assert page.items[0]["invocationStepId"] == "stp1"
    assert page.cursor == "next_token".encode()
    runtime_client.list_invocation_steps.assert_called_once_with(
        sessionIdentifier="sid",
        invocationIdentifier="iid",
        maxResults=10,
        nextToken="prev_token"
    )
