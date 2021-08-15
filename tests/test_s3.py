import pytest

import asyncio

from dataclasses import dataclass
from datetime import date, datetime
from fondat.aws import Config, Service
from fondat.aws.s3 import bucket_resource
from fondat.error import NotFoundError
from fondat.pagination import paginate
from typing import Optional, TypedDict
from uuid import uuid4


pytestmark = pytest.mark.asyncio


config = Config(
    endpoint_url="http://localhost:4566",
    aws_access_key_id="id",
    aws_secret_access_key="secret",
)


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def service():
    service = Service(name="s3", config=config)
    yield service
    await service.close()


@pytest.fixture(scope="function")
async def client(service):
    client = await service.client()
    yield client


async def _empty_bucket(client, bucket):
    while "Contents" in (response := await client.list_objects_v2(Bucket=bucket)):
        for item in response["Contents"]:
            await client.delete_object(Bucket=bucket, Key=item["Key"])


@pytest.fixture(scope="function")
async def bucket(client):
    name = str(uuid4())
    await client.create_bucket(Bucket=name)
    try:
        yield name
    finally:
        await _empty_bucket(client, name)
        await client.delete_bucket(Bucket=name)


async def test_crud(service, bucket):
    @dataclass
    class DC:
        id: str
        str_: Optional[str]
        dict_: Optional[TypedDict("TD", {"a": int})]
        list_: Optional[list[int]]
        set_: Optional[set[str]]
        int_: Optional[int]
        float_: Optional[float]
        bool_: Optional[bool]
        bytes_: Optional[bytes]
        date_: Optional[date]
        datetime_: Optional[datetime]

    resource = bucket_resource(
        service=service,
        bucket=bucket,
        key_type=str,
        value_type=DC,
    )
    id = "7af8410d-ffa3-4598-bac8-9ac0e488c9df"
    value = DC(
        id=id,
        str_="string",
        dict_={"a": 1},
        list_=[1, 2, 3],
        set_={"foo", "bar"},
        int_=1,
        float_=2.3,
        bool_=True,
        bytes_=b"12345",
        date_=date.fromisoformat("2019-01-01"),
        datetime_=datetime.fromisoformat("2019-01-01T01:01:01+00:00"),
    )
    r = resource[id]
    await r.put(value)
    assert await r.get() == value
    value.dict_ = {"a": 2}
    value.list_ = [2, 3, 4]
    value.set_ = None
    value.int_ = 2
    value.float_ = 1.0
    value.bool_ = False
    value.bytes_ = None
    value.date_ = None
    value.datetime_ = None
    await r.put(value)
    assert await r.get() == value
    await r.delete()
    with pytest.raises(NotFoundError):
        await r.get()


async def test_pagination(service, bucket):
    resource = bucket_resource(
        service=service,
        bucket=bucket,
        key_type=str,
        value_type=str,
    )
    assert len([v async for v in paginate(resource.get)]) == 0
    for n in range(0, 11):
        await resource[f"{n:04d}"].put("value")
    assert len([v async for v in paginate(resource.get)]) == 11
    page = await resource.get(limit=10)
    assert len(page.items) == 10
    page = await resource.get(limit=10, cursor=page.cursor)
    assert len(page.items) == 1


async def test_folder(service, bucket):
    resource = bucket_resource(
        service=service,
        bucket=bucket,
        folder="folder",
        key_type=str,
        value_type=str,
    )
    assert len([v async for v in paginate(resource.get)]) == 0
    count = 10
    for n in range(0, count):
        await resource[f"{n:04d}"].put(str(n))
    assert len([v async for v in paginate(resource.get)]) == count
    for n in range(0, count):
        assert await resource[f"{n:04d}"].get() == str(n)
