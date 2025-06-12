"""Unit tests for prompts."""

import pytest
from fondat.aws.bedrock.resources.prompts import PromptsResource, PromptResource
from fondat.aws.bedrock.domain import Prompt, PromptSummary
from fondat.pagination import Page
from fondat.error import NotFoundError, ForbiddenError
from tests.bedrock.unit.conftest import my_vcr
from tests.bedrock.unit.test_config import TEST_PROMPT_ID


@pytest.fixture
def prompts_resource(config):
    """Fixture para el recurso de prompts."""
    return PromptsResource(config_agent=config, cache_size=10, cache_expire=1)

@pytest.fixture
def prompt_resource(prompts_resource):
    """Fixture para un recurso de prompt específico."""
    return prompts_resource[TEST_PROMPT_ID]

@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_list_prompts.yaml")
async def test_list_prompts(prompts_resource):
    """Test para listar prompts."""
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
    """Test para listar prompts con cursor."""
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
async def test_get_prompt(prompts_resource):
    """Test para obtener detalles de un prompt."""
    try:
        # Primero obtener una lista de prompts
        page = await prompts_resource.get(max_results=1)
        assert page.items, "No prompts available for get_prompt test"
        id = page.items[0].id
        
        # Obtener el prompt específico
        prompt = await prompts_resource[id].get()
        assert prompt is not None, "Prompt not found"
        assert prompt.id == id, "Prompt ID mismatch"
        assert prompt.name is not None, "name missing"
        assert prompt.description is not None, "description missing"
        assert prompt.created_at is not None, "created_at missing"
        assert prompt.updated_at is not None, "updated_at missing"
    except Exception as e:
        pytest.fail(f"Failed to get prompt: {str(e)}")

@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_prompt_properties.yaml")
async def test_prompt_properties(prompt_resource):
    """Test para propiedades del recurso prompt."""
    try:
        # Test de la propiedad versions
        versions = prompt_resource.versions
        assert versions is not None
        assert versions._parent_id == TEST_PROMPT_ID
    except Exception as e:
        pytest.fail(f"Failed to test prompt properties: {str(e)}")

@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_get_nonexistent_prompt.yaml")
async def test_get_nonexistent_prompt(prompts_resource):
    """Test para obtener un prompt inexistente."""
    try:
        with pytest.raises((NotFoundError, ForbiddenError)):
            await prompts_resource["00000000-0000-0000-0000-000000000000"].get()
    except Exception as e:
        pytest.fail(f"Failed to test nonexistent prompt: {str(e)}")

@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_prompt_cache.yaml")
async def test_prompt_cache(prompts_resource):
    """Test para el cache de prompts."""
    try:
        page1 = await prompts_resource.get()
        page2 = await prompts_resource.get()
        assert page1.items == page2.items
    except Exception as e:
        pytest.fail(f"Failed to test prompt cache: {str(e)}") 