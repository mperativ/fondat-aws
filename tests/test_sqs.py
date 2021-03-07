import pytest

from dataclasses import dataclass
from datetime import date, datetime
from fondat.aws import Client, Config
from fondat.aws.sqs import queue_resource
from fondat.error import NotFoundError
from fondat.pagination import paginate
from typing import Optional, TypedDict
from uuid import uuid4


pytestmark = pytest.mark.asyncio


config = Config(
    endpoint_url="http://localhost:4566",
    aws_access_key_id="id",
    aws_secret_access_key="secret",
    region_name="us-east-1",
)


@pytest.fixture(scope="function")
async def client():
    async with Client(service_name="sqs", config=config) as client:
        yield client


@pytest.fixture(scope="function")
async def queue_url(client) -> str:
    url = (await client.create_queue(QueueName=str(uuid4())))["QueueUrl"]
    try:
        yield url
    finally:
        await client.delete_queue(QueueUrl=url)


async def test_send_receive(client, queue_url):
    @dataclass
    class DC:
        n: int

    queue = queue_resource(client=client, queue_url=queue_url, message_type=DC)
    for n in range(0, 3):
        await queue.send(DC(n=n))
    for n in range(0, 3):
        assert await queue.receive() == DC(n=n)
    assert await queue.receive() is None
