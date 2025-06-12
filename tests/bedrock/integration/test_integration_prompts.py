from datetime import datetime
import json
import pytest

from fondat.aws.bedrock import prompts_resource
from fondat.aws.client import Config
from tests.bedrock.integration.conftest import my_vcr

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

@pytest.fixture(scope="module")
def cfg():
    return Config(region_name="us-east-2")

@pytest.fixture(scope="module")
def prompts(cfg):
    return prompts_resource(config_agent=cfg)

@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_list_prompts.yaml")
async def test_list_prompts(prompts):
    """Test listing prompts."""
    page = await prompts.get(max_results=20)
    assert page.items, "No prompts returned"
    for prompt in page.items:
        assert prompt.id, "id missing"
        assert prompt.name, "name missing"
        assert prompt.description is not None, "description missing"
        assert prompt.created_at is not None, "created_at missing"
    return page.items[0].id

@pytest.mark.asyncio
async def test_get_prompt(prompts):
    """Test getting a specific prompt."""
    page = await prompts.get(max_results=1)
    assert page.items, "No prompts available for get_prompt test"
    id = page.items[0].id
    prompt = await prompts[id].get()
    assert prompt is not None, "Prompt not found"
    assert prompt.id == id, "Prompt ID mismatch"
    assert prompt.name is not None, "name missing"
    assert prompt.description is not None, "description missing"
    assert prompt.created_at is not None, "created_at missing"
    assert prompt.updated_at is not None, "updated_at missing"
