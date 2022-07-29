import asyncio
import fondat.aws.client
import pytest

from fondat.aws.secretsmanager import Secret, secrets_resource
from fondat.error import BadRequestError, NotFoundError
from pytest import fixture
from uuid import uuid4


@fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@fixture(scope="module")
async def resource():
    yield secrets_resource()


async def test_string_binary(resource):
    name = str(uuid4())
    with pytest.raises(NotFoundError):
        await resource[name].delete()
    with pytest.raises(NotFoundError):
        await resource[name].put(Secret(value="something"))
    await resource.post(name=name, secret=Secret(value="string"))
    assert (await resource[name].get()).value == "string"
    await resource[name].put(Secret(value=b"binary"))
    assert (await resource[name].get()).value == b"binary"
    await resource[name].delete()
    with pytest.raises(BadRequestError):
        await resource[name].get()


async def test_binary_string(resource):
    name = str(uuid4())
    await resource.post(name=name, secret=Secret(value=b"binary"))
    assert (await resource[name].get()).value == b"binary"
    await resource[name].put(Secret(value="string"))
    assert (await resource[name].get()).value == "string"
    await resource[name].delete()


async def test_get_cache():
    async with fondat.aws.client.create_client("secretsmanager") as client:
        resource = secrets_resource(cache_size=10, cache_expire=10)
        name = str(uuid4())
        secret = Secret(value=name)
        await client.create_secret(Name=name, SecretString=secret.value)
        assert await resource[name].get() == secret  # caches secret
        await client.delete_secret(SecretId=name)
        assert await resource[name].get() == secret  # still cached


async def test_put_get_cache():
    async with fondat.aws.client.create_client("secretsmanager") as client:
        resource = secrets_resource(cache_size=10, cache_expire=10)
        name = str(uuid4())
        secret = Secret(value=name)
        await resource.post(name=name, secret=secret)  # caches secret
        await client.delete_secret(SecretId=name)
        assert await resource[name].get() == secret  # still cached


async def test_delete_cache():
    resource = secrets_resource(cache_size=10, cache_expire=10)
    name = str(uuid4())
    secret = Secret(value=name)
    await resource.post(name=name, secret=secret)  # caches secret
    await resource[name].get()  # still cached
    await resource[name].delete()  # deletes cached row
    with pytest.raises(BadRequestError):  # marked as deleted
        await resource[name].get()


async def test_get_cache_evict():
    async with fondat.aws.client.create_client("secretsmanager") as client:
        resource = secrets_resource(cache_size=1, cache_expire=10)
        name1 = str(uuid4())
        secret1 = Secret(value=name1)
        await client.create_secret(Name=name1, SecretString=secret1.value)
        name2 = str(uuid4())
        secret2 = Secret(value=name2)
        await client.create_secret(Name=name2, SecretString=secret2.value)
        assert await resource[name1].get() == secret1
        assert await resource[name2].get() == secret2
        await client.delete_secret(SecretId=name1)
        await client.delete_secret(SecretId=name2)
        with pytest.raises(BadRequestError):
            await resource[name1].get()  # evicted and marked deleted
        assert await resource[name2].get() == secret2  # still cached
