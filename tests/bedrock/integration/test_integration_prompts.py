from datetime import datetime
import json
import pytest

from fondat.aws.bedrock import prompts_resource
from fondat.aws.bedrock.domain import Prompt, PromptSummary
from fondat.aws.bedrock.resources.prompts import PromptResource
from fondat.aws.client import Config
from tests.bedrock.integration.conftest import my_vcr, aws_session

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_integration_list_prompts.yaml")
async def test_integration_list_prompts(aws_session):
    """Test listing prompts."""
    prompts = prompts_resource(config_agent=aws_session.config_agent)
    page = await prompts.get(max_results=20)
    assert len(page.items) > 0
    assert isinstance(page.items[0], PromptSummary)
    assert page.items[0].id is not None
    assert page.items[0].name is not None
    assert page.items[0].created_at is not None
    assert page.items[0].description is not None
    assert page.items[0]._factory is not None

@pytest.mark.asyncio
@pytest.mark.vcr(vcr=my_vcr, cassette_name="test_integration_get_prompt.yaml")
async def test_integration_get_prompt(aws_session):
    """Test getting a specific prompt."""
    prompts = prompts_resource(config_agent=aws_session.config_agent)
    page = await prompts.get(max_results=1)
    prompt = await prompts[page.items[0].id].get()
    assert prompt is not None
    assert isinstance(prompt, Prompt)
    assert prompt.id is not None
    assert prompt.name is not None
    assert prompt.created_at is not None
    assert prompt.updated_at is not None
    assert prompt.description is not None
    assert prompt._factory is not None
    assert isinstance(prompt.resource, PromptResource)