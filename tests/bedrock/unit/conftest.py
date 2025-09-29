import os
import boto3
import pytest
import vcr
import logging
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from fondat.aws.client import Config
from fondat.aws.bedrock.cache import BedrockCache

logger = logging.getLogger(__name__)


# Configure VCR to use unit test cassettes
CASSETTE_DIR = Path(__file__).parent / "cassettes" / "bedrock"
CASSETTE_DIR.mkdir(parents=True, exist_ok=True)


def get_vcr(force_record=False):
    """Get VCR instance with appropriate configuration."""

    def before_record_response(response):
        """Modify response before recording."""
        # Remove sensitive headers from response
        headers = dict(response.get("headers", {}))
        for header in [
            "authorization",
            "x-amz-security-token",
            "x-amz-date",
            "x-amz-content-sha256",
        ]:
            if header in headers:
                headers[header] = "DUMMY"

        return {
            "status": response.get("status", 200),
            "headers": headers,
            "body": response.get("body", b""),
        }

    return vcr.VCR(
        cassette_library_dir=str(CASSETTE_DIR),
        # In local runs, force_record=True should record; use 'all' to re-record
        record_mode="none" if os.getenv("CI") else ("all" if force_record else "new_episodes"),
        match_on=["uri", "method"],
        filter_headers=[
            "authorization",
            "x-amz-security-token",
            "x-amz-date",
            "x-amz-content-sha256",
        ],
        before_record_response=before_record_response,
    )


# Create VCR instances
my_vcr = get_vcr()
force_record_vcr = get_vcr(force_record=True)


@pytest.fixture
def mock_agent_client():
    client = AsyncMock()
    with patch("fondat.aws.bedrock.resources.prompts.agent_client") as mock:
        mock.return_value.__aenter__.return_value = client
        yield client


@pytest.fixture
def mock_runtime_client():
    client = AsyncMock()
    with patch("fondat.aws.bedrock.resources.prompts.runtime_client") as mock:
        mock.return_value.__aenter__.return_value = client
        yield client


@pytest.fixture
def bedrock_cache():
    """Fixture to provide a BedrockCache instance."""
    return BedrockCache(cache_size=10, cache_expire=300)


@pytest.fixture
def mock_datetime():
    """Fixture to provide a fixed datetime for testing."""
    return datetime(2024, 1, 1, tzinfo=timezone.utc)


@pytest.fixture(scope="session")
def config():
    """Fixture to provide AWS configuration."""
    region = os.getenv("AWS_REGION", "us-east-2")
    profile = os.getenv("AWS_PROFILE", "mperativ-admin")

    # Create a session to get credentials
    session = boto3.Session(profile_name=profile, region_name=region)
    credentials = session.get_credentials()

    # Prefer using the profile so botocore can auto-refresh SSO credentials.
    if profile:
        return Config(profile=profile, region_name=region)

    # Fallbacks
    if not credentials:
        return Config(region_name=region)
    return Config(region_name=region)


@pytest.fixture(scope="session")
def aws_session(config):
    """Fixture to provide AWS session."""
    return boto3.Session(
        region_name=config.region_name,
        aws_access_key_id=config.aws_access_key_id,
        aws_secret_access_key=config.aws_secret_access_key,
        aws_session_token=config.aws_session_token,
    )


@pytest.fixture(scope="session")
def credentials(config):
    """Fixture to provide AWS credentials."""
    return {
        "aws_access_key_id": config.aws_access_key_id,
        "aws_secret_access_key": config.aws_secret_access_key,
        "aws_session_token": config.aws_session_token,
    }


@pytest.fixture(autouse=True)
async def cleanup_sessions_unit(config):
    """
    Fixture that automatically cleans up all sessions after each unit test.
    This ensures no sessions are left behind from test runs.
    """
    yield
    
    try:
        from tests.bedrock.unit.test_config import TEST_AGENT_ID
        from fondat.aws.bedrock.resources.sessions import SessionsResource
        
        sessions_resource = SessionsResource(
            agent_id=TEST_AGENT_ID, config_runtime=config, cache_size=10, cache_expire=1
        )
        
        sessions_page = await sessions_resource.get(max_results=100)
        for session_summary in sessions_page.items:
            try:
                session_resource_instance = sessions_resource[session_summary.session_id]
                await session_resource_instance.delete()
            except Exception as e:
                logger.warning(f"Failed to delete unit test session {session_summary.session_id}: {e}")
                
    except Exception as e:
        logger.warning(f"Error during unit test session cleanup: {e}")
