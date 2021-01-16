import pytest

from dataclasses import dataclass
from datetime import date, datetime
from fondat.aws import Config
from fondat.aws.s3 import Client, bucket_resource
from fondat.error import NotFoundError
from fondat.paging import paginate
from typing import Optional, TypedDict


pytestmark = pytest.mark.asyncio


config = Config(
    endpoint_url="http://localhost:4566",
    aws_access_key_id="id",
    aws_secret_access_key="secret",
)


@pytest.fixture(scope="function")
async def client():
    async with Client(config) as client:
        yield client

async def _delete_all(resource):
    async for key in paginate(resource.get):
        await resource[key].delete()


async def test_crud(client):
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
        client=client,
        bucket="fondat",
        key_type=str,
        value_type=DC,
    )
    await _delete_all(resource)
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
    await _delete_all(resource)


async def test_pagination(client):
    resource = bucket_resource(
        client=client,
        bucket="fondat",
        key_type=str,
        value_type=str,
    )
    await _delete_all(resource)
    assert len([v async for v in paginate(resource.get)]) == 0
    for n in range(0, 11):
        await resource[f"{n:04d}"].put("value")
    assert len([v async for v in paginate(resource.get)]) == 11
    page = await resource.get(limit=10)
    assert len(page.items) == 10
    page = await resource.get(limit=10, cursor=page.cursor)
    assert len(page.items) == 1
    await _delete_all(resource)


async def test_folder(client):
    resource = bucket_resource(
        client=client,
        bucket="fondat",
        folder="folder",
        key_type=str,
        value_type=str,
    )
    await _delete_all(resource)
    assert len([v async for v in paginate(resource.get)]) == 0
    count = 10
    for n in range(0, count):
        await resource[f"{n:04d}"].put(str(n))
    assert len([v async for v in paginate(resource.get)]) == count
    for n in range(0, count):
        assert await resource[f"{n:04d}"].get() == str(n)
    await _delete_all(resource)
