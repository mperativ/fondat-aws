"""Common fixtures for unit tests."""

from datetime import datetime, timezone
import os
from pathlib import Path
import boto3
import pytest
import vcr
from fondat.aws.client import Config
from fondat.aws.bedrock.cache import BedrockCache
from unittest.mock import AsyncMock, patch

# Configure VCR to use unit test cassettes
CASSETTE_DIR = Path(__file__).parent / "cassettes" / "bedrock"
CASSETTE_DIR.mkdir(parents=True, exist_ok=True)

def get_vcr(force_record=False):
    """Get VCR instance with appropriate configuration."""
    def before_record_response(response):
        """Modify response before recording."""
        # Remove sensitive headers from response
        headers = dict(response.get('headers', {}))
        for header in ['authorization', 'x-amz-security-token', 'x-amz-date', 'x-amz-content-sha256']:
            if header in headers:
                headers[header] = 'DUMMY'
        
        return {
            'status': response.get('status', 200),
            'headers': headers,
            'body': response.get('body', b''),
        }

    return vcr.VCR(
        cassette_library_dir=str(CASSETTE_DIR),
        record_mode='none' if os.getenv('CI') else ('once' if force_record else 'new_episodes'),
        match_on=['uri', 'method'],
        filter_headers=['authorization', 'x-amz-security-token', 'x-amz-date', 'x-amz-content-sha256'],
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
def vcr_playback():
    """Fixture to provide VCR playback functionality."""
    return my_vcr

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
    
    # If no credentials are available, use mock credentials
    if not credentials:
        return Config(
            region_name=region,
            aws_access_key_id="DUMMY_ACCESS_KEY",
            aws_secret_access_key="DUMMY_SECRET_KEY",
            aws_session_token="DUMMY_SESSION_TOKEN",
        )
    
    return Config(
        region_name=region,
        aws_access_key_id=credentials.access_key,
        aws_secret_access_key=credentials.secret_key,
        aws_session_token=credentials.token,
    )

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