import pytest
from botocore.exceptions import HTTPClientError
from datetime import datetime
import logging

from fondat.pagination import Page
from fondat.error import NotFoundError
from fondat.aws.bedrock.resources.sessions import SessionsResource, SessionResource
from fondat.aws.bedrock.domain import Session, SessionSummary, Invocation, InvocationStepSummary

from tests.bedrock.unit.conftest import my_vcr
from tests.bedrock.unit.test_config import TEST_AGENT_ID

logger = logging.getLogger(__name__)


@pytest.fixture
def sessions_resource(config):
    """Fixture to provide sessions resource."""
    return SessionsResource(
        agent_id=TEST_AGENT_ID, config_runtime=config, cache_size=10, cache_expire=1
    )


@pytest.fixture
async def session_resource(sessions_resource):
    """Provide a session resource for testing."""
    # Create a new session for testing
    session = await sessions_resource.create()
    session_resource = sessions_resource[session.session_id]
    
    try:
        yield session_resource
    finally:
        try:
            await session_resource.delete()
        except Exception as e:
            logger.warning(f"Failed to delete unit test session {session.session_id}: {e}")


@pytest.fixture
async def invocations_resource(session_resource):
    """Fixture to provide invocations resource."""
    session = session_resource
    return session.invocations


@pytest.fixture
async def invocation_resource(invocations_resource):
    """Fixture to provide invocation resource."""
    # Create a new invocation for testing
    invocations = invocations_resource
    invocation = await invocations.create()
    # Get the InvocationResource using the invocation ID
    invocation_resource = invocations[invocation.invocation_id]
    
    try:
        yield invocation_resource
    finally:
        # Note: Invocations are automatically cleaned up when the session is deleted
        # So we don't need to explicitly delete them here
        pass


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_list_sessions.yaml")
async def test_list_sessions(sessions_resource):
    """Test listing sessions."""
    try:
        page = await sessions_resource.get(max_results=5)
        assert isinstance(page.items, list)
        if page.items:
            assert isinstance(page.items[0], SessionSummary)
            assert page.items[0].session_id
            # memory_id is optional and can be empty string
            assert isinstance(page.items[0].memory_id, str)
            assert page.items[0].session_start_time
            assert page.items[0].session_expiry_time
            assert isinstance(page.items[0].summary_text, str)
    except Exception as e:
        pytest.fail(f"Failed to list sessions: {str(e)}")


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_session_lifecycle.yaml")
async def test_list_sessions_with_cursor(sessions_resource):
    """Test listing sessions with cursor."""
    try:
        # Get first page
        page1 = await sessions_resource.get(max_results=5)
        if not page1.items:
            pytest.skip("No sessions available")

        # Get second page using cursor
        page2 = await sessions_resource.get(max_results=5, cursor=page1.cursor)
        assert isinstance(page2.items, list)
        if page2.items:
            assert page2.items[0].session_id != page1.items[0].session_id
    except Exception as e:
        pytest.fail(f"Failed to list sessions with cursor: {str(e)}")


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_session_lifecycle.yaml")
async def test_create_session(sessions_resource):
    """Test creating a session."""
    try:
        session = await sessions_resource.create()
        assert isinstance(session, Session)
        assert session.session_id
        assert session.session_status == "ACTIVE"
    except Exception as e:
        pytest.fail(f"Failed to create session: {str(e)}")


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_session_lifecycle.yaml")
async def test_get_session(session_resource):
    """Test getting session."""
    session = await session_resource.get()
    assert session is not None

    # Validate required fields
    assert hasattr(session, "session_id")
    assert hasattr(session, "created_at")
    assert hasattr(session, "session_status")

    # Validate session properties
    assert isinstance(session, Session)
    assert isinstance(session.resource, SessionResource)
    assert isinstance(session.created_at, datetime)
    if hasattr(session, "session_metadata"):
        assert isinstance(session.session_metadata, dict)


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_session_lifecycle.yaml")
async def test_delete_session(session_resource):
    """Test deleting a session."""
    try:
        session = session_resource
        current_session = await session.get()
        assert isinstance(current_session, Session)
        assert current_session.session_status == "ACTIVE"
        await session.delete()
        with pytest.raises(NotFoundError):
            await session.get()
    except Exception as e:
        pytest.fail(f"Failed to delete session: {str(e)}")


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_invocation_lifecycle.yaml")
async def test_list_invocations(invocations_resource):
    """Test listing invocations."""
    try:
        invocations = invocations_resource
        page = await invocations.get(max_results=5)
        assert isinstance(page.items, list)
        if page.items:
            assert isinstance(page.items[0], Invocation)
            assert page.items[0].invocation_id
            assert page.items[0].status
    except Exception as e:
        pytest.fail(f"Failed to list invocations: {str(e)}")


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_invocation_lifecycle.yaml")
async def test_create_invocation(invocations_resource):
    """Test creating an invocation."""
    try:
        invocations = invocations_resource
        invocation = await invocations.create()
        assert isinstance(invocation, Invocation)
        assert invocation.invocation_id
        assert invocation.session_id
        assert invocation.created_at
    except Exception as e:
        pytest.fail(f"Failed to create invocation: {str(e)}")


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_invocation_lifecycle.yaml")
async def test_get_invocation(invocation_resource):
    """Test getting invocation details."""
    try:
        invocation = invocation_resource
        # Get the invocation steps
        steps = await invocation.get_steps()
        assert isinstance(steps, Page)
        assert isinstance(steps.items, list)
        if steps.items:
            assert isinstance(steps.items[0], InvocationStepSummary)
            assert steps.items[0].invocation_step_id
            assert steps.items[0].invocation_id
            assert steps.items[0].session_id
            assert steps.items[0].invocation_step_time is not None
    except Exception as e:
        pytest.fail(f"Failed to get invocation: {str(e)}")


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_invocation_steps.yaml")
async def test_get_invocation_steps(invocation_resource):
    """Test getting invocation steps."""
    try:
        invocation = invocation_resource
        steps = await invocation.get_steps()
        assert isinstance(steps, Page)
        assert isinstance(steps.items, list)
        if steps.items:
            assert isinstance(steps.items[0], InvocationStepSummary)
            assert steps.items[0].invocation_step_id
            assert steps.items[0].invocation_id
            assert steps.items[0].session_id
            assert steps.items[0].invocation_step_time is not None
    except Exception as e:
        pytest.fail(f"Failed to get invocation steps: {str(e)}")


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_session_lifecycle.yaml")
async def test_session_cache(sessions_resource):
    """Test session list caching."""
    try:
        # First call should hit the API
        page1 = await sessions_resource.get()

        # Second call should use cache
        page2 = await sessions_resource.get()

        # Results should be the same
        assert page1.items == page2.items
    except Exception as e:
        pytest.fail(f"Failed to test session cache: {str(e)}")


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_session_lifecycle.yaml")
async def test_get_nonexistent_session(sessions_resource):
    """Test getting a nonexistent session."""
    try:
        with pytest.raises(NotFoundError):
            # Use a valid UUID format but non-existent ID
            await sessions_resource["00000000-0000-0000-0000-000000000000"].get()
    except Exception as e:
        pytest.fail(f"Failed to test nonexistent session: {str(e)}")


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_invocation_lifecycle.yaml")
async def test_invocation_error_handling(invocations_resource):
    """Test invocation error handling."""
    try:
        invocations = invocations_resource
        # Test that getting steps for a non-existent invocation raises NotFoundError
        with pytest.raises(NotFoundError):
            await invocations["00000000-0000-0000-0000-000000000000"].get_steps()
    except HTTPClientError as e:
        # If we get an HTTPClientError due to AWS credentials, skip the test
        pytest.skip(f"Skipping test due to AWS credentials error: {str(e)}")
    except Exception as e:
        pytest.fail(f"Failed to test invocation error handling: {str(e)}")
