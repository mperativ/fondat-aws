import pytest

from dataclasses import dataclass
from fondat.aws import Config, Service
from fondat.aws.sqs import queue_resource
from uuid import uuid4


pytestmark = pytest.mark.asyncio


config = Config(
    endpoint_url="http://localhost:4566",
    aws_access_key_id="id",
    aws_secret_access_key="secret",
    region_name="us-east-1",
)


@pytest.fixture(scope="function")
async def service():
    service = Service(name="sqs", config=config)
    yield service
    await service.close()


@pytest.fixture(scope="function")
async def queue_url(service) -> str:
    client = await service.client()
    url = (await client.create_queue(QueueName=str(uuid4())))["QueueUrl"]
    try:
        yield url
    finally:
        await client.delete_queue(QueueUrl=url)


async def test_send_receive(service, queue_url):
    @dataclass
    class DC:
        n: int

    queue = queue_resource(service=service, queue_url=queue_url, message_type=DC)
    for n in range(0, 3):
        await queue.send(DC(n=n))
    for n in range(0, 3):
        assert await queue.receive() == DC(n=n)
    assert await queue.receive() is None
