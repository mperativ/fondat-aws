import pytest
from fondat.aws.bedrock.resources.prompts import PromptsResource, PromptResource
from fondat.aws.bedrock.domain import PromptSummary, Prompt
from fondat.error import NotFoundError, ForbiddenError
from tests.bedrock.unit.conftest import my_vcr
from tests.bedrock.unit.test_config import TEST_PROMPT_ID
from datetime import datetime


@pytest.fixture
def prompts_resource(config):
    """Fixture for the prompts resource."""
    return PromptsResource(config_agent=config, cache_size=10, cache_expire=1)


@pytest.fixture
def prompt_resource(config):
    """Provide a prompt resource for testing."""
    return PromptResource(
        id=TEST_PROMPT_ID,
        config_agent=config,
    )


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_list_prompts.yaml")
async def test_list_prompts(prompts_resource):
    """Test listing prompts."""
    try:
        page = await prompts_resource.get(max_results=5)
        assert isinstance(page.items, list)
        if page.items:
            assert isinstance(page.items[0], PromptSummary)
            assert page.items[0].id
            assert page.items[0].name
    except Exception as e:
        pytest.fail(f"Failed to list prompts: {str(e)}")


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_list_prompts.yaml")
async def test_list_prompts_with_cursor(prompts_resource):
    """Test listing prompts with cursor."""
    try:
        page1 = await prompts_resource.get(max_results=5)
        if not page1.items:
            pytest.skip("No prompts available")
        page2 = await prompts_resource.get(max_results=5, cursor=page1.cursor)
        assert isinstance(page2.items, list)
        if page2.items:
            assert isinstance(page2.items[0], PromptSummary)
    except Exception as e:
        pytest.fail(f"Failed to list prompts with cursor: {str(e)}")


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_get_prompt.yaml")
async def test_get_prompt(prompt_resource):
    """Test getting prompt."""
    try:
        prompt = await prompt_resource.get()
        assert prompt is not None
        assert isinstance(prompt, Prompt)
        assert isinstance(prompt.resource, PromptResource)
        assert prompt.id == TEST_PROMPT_ID
        assert prompt.created_at is not None
    except ForbiddenError:
        pytest.skip("Skipping test due to IAM permissions")
    except Exception as e:
        pytest.fail(f"Failed to get prompt: {str(e)}")


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_prompt_properties.yaml")
async def test_prompt_properties(prompt_resource):
    """Test prompt properties."""
    try:
        versions = prompt_resource.versions
        assert versions is not None
        assert versions._parent_id == TEST_PROMPT_ID
    except Exception as e:
        pytest.fail(f"Failed to test prompt properties: {str(e)}")


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_get_nonexistent_prompt.yaml")
async def test_get_nonexistent_prompt(prompts_resource):
    """Test getting a nonexistent prompt."""
    try:
        with pytest.raises((NotFoundError, ForbiddenError)):
            await prompts_resource["00000000-0000-0000-0000-000000000000"].get()
    except Exception as e:
        pytest.fail(f"Failed to test nonexistent prompt: {str(e)}")


@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_prompt_cache.yaml")
async def test_prompt_cache(prompts_resource):
    """Test prompt cache."""
    try:
        page1 = await prompts_resource.get()
        page2 = await prompts_resource.get()
        assert page1.items == page2.items
    except Exception as e:
        pytest.fail(f"Failed to test prompt cache: {str(e)}")
