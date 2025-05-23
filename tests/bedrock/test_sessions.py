"""Tests for bedrock sessions functionality."""

from fondat.aws.bedrock.resources.agents import AgentsResource
from fondat.pagination import Page


async def test_create_session(mock_clients, config):
    """Test creating a new agent session with optional tags."""
    _, runtime_client = mock_clients
    runtime_client.create_session.return_value = {"sessionId": "sid"}
    res = await AgentsResource(config_agent=config, config_runtime=config)[
        "agent-1"
    ].sessions.create(tags={"a": "b"})
    assert res["sessionId"] == "sid"
    runtime_client.create_session.assert_called_once_with(tags={"a": "b"})


async def test_get_session(mock_clients, config):
    """Test retrieving session details by ID."""
    _, runtime_client = mock_clients
    runtime_client.get_session.return_value = {"sessionId": "sid"}
    res = await AgentsResource(config_agent=config, config_runtime=config)[
        "agent-1"
    ].sessions.get("sid")
    assert res["sessionId"] == "sid"
    runtime_client.get_session.assert_called_once_with(sessionIdentifier="sid")


async def test_delete_session(mock_clients, config):
    """Test deleting a session by ID."""
    _, runtime_client = mock_clients
    await AgentsResource(config_agent=config, config_runtime=config)["agent-1"].sessions.delete(
        "sid"
    )
    runtime_client.delete_session.assert_called_once_with(sessionIdentifier="sid")


async def test_end_session(mock_clients, config):
    """Test ending an active session."""
    _, runtime_client = mock_clients
    runtime_client.end_session.return_value = {"status": "ENDED"}
    res = await AgentsResource(config_agent=config, config_runtime=config)[
        "agent-1"
    ].sessions.end("sid")
    assert res["status"] == "ENDED"
    runtime_client.end_session.assert_called_once_with(sessionIdentifier="sid")


async def test_update_session(mock_clients, config):
    """Test updating session metadata."""
    _, runtime_client = mock_clients
    runtime_client.update_session.return_value = {
        "createdAt": "2024-01-01T00:00:00Z",
        "lastUpdatedAt": "2024-01-01T00:00:00Z",
        "sessionArn": "arn:aws:bedrock:us-east-2:123456789012:session/sid",
        "sessionId": "sid",
        "sessionStatus": "ACTIVE"
    }
    res = await AgentsResource(config_agent=config, config_runtime=config)[
        "agent-1"
    ].sessions.update("sid", sessionMetadata={"k": "v"})
    assert res["sessionId"] == "sid"
    assert res["sessionStatus"] == "ACTIVE"
    runtime_client.update_session.assert_called_once_with(
        sessionIdentifier="sid",
        sessionMetadata={"k": "v"}
    )


async def test_create_invocation(mock_clients, config):
    """Test creating a new invocation within a session."""
    _, runtime_client = mock_clients
    runtime_client.create_invocation.return_value = {
        "createdAt": "2024-01-01T00:00:00Z",
        "invocationId": "iid",
        "sessionId": "sid"
    }
    res = await AgentsResource(config_agent=config, config_runtime=config)[
        "agent-1"
    ].sessions.invocations.create(
        sessionIdentifier="sid",
        invocationId="iid",
        description="Test invocation"
    )
    assert res["invocationId"] == "iid"
    assert res["sessionId"] == "sid"
    runtime_client.create_invocation.assert_called_once_with(
        sessionIdentifier="sid",
        invocationId="iid",
        description="Test invocation"
    )


async def test_put_step(mock_clients, config):
    """Test adding a step to an invocation."""
    _, runtime_client = mock_clients
    runtime_client.put_invocation_step.return_value = {"invocationStepId": "stp"}
    from datetime import datetime

    res = await AgentsResource(config_agent=config, config_runtime=config)[
        "agent-1"
    ].sessions.invocations.put_step(
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


async def test_get_step(mock_clients, config):
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
    res = await AgentsResource(config_agent=config, config_runtime=config)[
        "agent-1"
    ].sessions.invocations.get_step(
        sessionIdentifier="sid",
        invocationIdentifier="iid",
        invocationStepId="stp"
    )
    assert res["invocationStep"]["invocationStepId"] == "stp"
    assert res["invocationStep"]["invocationId"] == "iid"
    assert res["invocationStep"]["sessionId"] == "sid"
    runtime_client.get_invocation_step.assert_called_once_with(
        sessionIdentifier="sid",
        invocationIdentifier="iid",
        invocationStepId="stp"
    )


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
    page = await AgentsResource(config_agent=config, config_runtime=config)[
        "agent-1"
    ].sessions.invocations.list_steps(
        sessionIdentifier="sid",
        invocationIdentifier="iid",
        max_results=10,
        cursor="prev_token"
    )
    assert isinstance(page, Page)
    assert len(page.items) == 1
    assert page.items[0]["invocationStepId"] == "stp1"
    assert page.items[0]["invocationId"] == "iid"
    assert page.items[0]["sessionId"] == "sid"
    runtime_client.list_invocation_steps.assert_called_once_with(
        sessionIdentifier="sid",
        invocationIdentifier="iid",
        maxResults=10,
        nextToken="prev_token"
    )


async def test_list_invocations(mock_clients, config):
    """Test listing all invocations in a session with pagination."""
    _, runtime_client = mock_clients
    runtime_client.list_invocations.return_value = {
        "invocationSummaries": [
            {
                "createdAt": "2024-01-01T00:00:00Z",
                "invocationId": "iid",
                "sessionId": "sid"
            }
        ],
        "nextToken": "next_token"
    }
    page = await AgentsResource(config_agent=config, config_runtime=config)[
        "agent-1"
    ].sessions.invocations.list(
        sessionIdentifier="sid",
        max_results=10,
        cursor="prev_token"
    )
    assert isinstance(page, Page)
    assert len(page.items) == 1
    assert page.items[0]["invocationId"] == "iid"
    assert page.items[0]["sessionId"] == "sid"
    assert page.items[0]["createdAt"] == "2024-01-01T00:00:00Z"
    runtime_client.list_invocations.assert_called_once_with(
        sessionIdentifier="sid",
        maxResults=10,
        nextToken="prev_token"
    )
