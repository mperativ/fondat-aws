import pytest
from typing import Dict, Any

from fondat.security import Policy
from fondat.resource import resource
from fondat.aws.bedrock.decorators import operation


@resource
class TestResource:
    __test__ = False
    def __init__(self, policies=None):
        self.policies = policies

    @operation("get")
    async def simple_get(self) -> str:
        return "success"

    @operation("post")
    async def test_with_args(self, arg1: str, arg2: str) -> str:
        return f"{arg1}_{arg2}"

    @operation("put")
    async def test_with_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return data

    @operation("get", policies=lambda self: [self.policies] if self.policies else None)
    async def test_with_policies(self) -> str:
        return "success"


@pytest.mark.asyncio
async def test_operation_decorator():
    # Test with no policies
    resource = TestResource()
    assert await resource.simple_get() == "success"


@pytest.mark.asyncio
async def test_operation_decorator_with_args():
    # Test function with arguments
    resource = TestResource()
    assert await resource.test_with_args("test", "args") == "test_args"


@pytest.mark.asyncio
async def test_operation_decorator_with_dict():
    # Test function with dictionary argument
    resource = TestResource()
    data = {"key1": "value1", "key2": "value2"}
    result = await resource.test_with_dict(data)
    assert result == data


@pytest.mark.asyncio
async def test_operation_decorator_with_policies():
    # Test with policies
    policy = Policy()
    resource = TestResource(policies=policy)
    assert await resource.test_with_policies() == "success"
