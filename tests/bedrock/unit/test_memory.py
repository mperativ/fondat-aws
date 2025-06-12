import pytest
from fondat.aws.bedrock.domain import MemoryContents, SessionSummary
from fondat.aws.bedrock.resources.memory import MemoryResource
from tests.bedrock.unit.conftest import my_vcr
from tests.bedrock.unit.test_config import TEST_AGENT_ID, TEST_AGENT_ALIAS_ID

MEMORY_TYPE = "SESSION_SUMMARY"
MEMORY_ID = "test-memory"


@pytest.fixture
def memory_resource(config):
    """Provide a memory resource for a specific agent."""
    return MemoryResource(
        agent_id=TEST_AGENT_ID, config_runtime=config, cache_size=10, cache_expire=1
    )


@pytest.fixture
def specific_memory_resource(memory_resource):
    """Provide a specific memory resource with a test memory ID."""
    return memory_resource[MEMORY_ID]


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_get_memory.yaml")
async def test_get_memory(specific_memory_resource):
    """Test getting memory."""
    memory = await specific_memory_resource.get(
        agentAliasId=TEST_AGENT_ALIAS_ID, memoryType=MEMORY_TYPE
    )
    assert memory is not None
    assert isinstance(memory.memory_contents, list)

    # Validate memory contents structure
    for content in memory.memory_contents:
        assert hasattr(content, "session_summary")
        session_summary = content.session_summary
        assert isinstance(session_summary, SessionSummary)
        assert hasattr(session_summary, "memory_id")
        assert hasattr(session_summary, "session_id")
        assert hasattr(session_summary, "session_start_time")
        assert hasattr(session_summary, "session_expiry_time")
        assert hasattr(session_summary, "summary_text")
    assert isinstance(memory, MemoryContents)
    assert isinstance(memory.resource, MemoryResource)


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_delete_memory.yaml")
async def test_delete_memory(specific_memory_resource):
    """Test deleting memory."""
    await specific_memory_resource.delete(agentAliasId=TEST_AGENT_ALIAS_ID)


@pytest.mark.asyncio
async def test_memory_cache(specific_memory_resource):
    """Test memory caching."""
    # First call should hit the API
    memory1 = await specific_memory_resource.get(
        agentAliasId=TEST_AGENT_ALIAS_ID, memoryType=MEMORY_TYPE
    )
    assert memory1 is not None

    # Second call should use cache
    memory2 = await specific_memory_resource.get(
        agentAliasId=TEST_AGENT_ALIAS_ID, memoryType=MEMORY_TYPE
    )
    assert memory2 is not None
    assert memory1 == memory2
