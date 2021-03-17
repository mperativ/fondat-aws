import pytest

from dataclasses import dataclass
from datetime import date, datetime
from fondat.aws import Client, Config
from fondat.aws.cloudwatch import cloudwatch_resource
from fondat.error import NotFoundError
from fondat.monitoring import Counter, Gauge, Absolute

pytestmark = pytest.mark.asyncio


config = Config(
    endpoint_url="http://localhost:4566",
    aws_access_key_id="id",
    aws_secret_access_key="secret",
    region_name="us-east-1",
)


@pytest.fixture(scope="function")
async def client():
    async with Client(service_name="cloudwatch", config=config) as client:
        yield client

@pytest.fixture(scope="function")
async def metirc_type(client):
    _now = lambda: datetime.now()
    type_name = Counter(_now())
    yield type_name


async def test_put_metric (client, metirc_type):
    assert metirc_type.name == "counter"
