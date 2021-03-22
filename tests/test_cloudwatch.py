import pytest

from dataclasses import dataclass
from datetime import date, datetime
from fondat.aws import Client, Config
from fondat.aws.cloudwatch import cloudwatch_resource
from fondat.error import NotFoundError
from fondat.monitoring import Measurement, Counter, Gauge, Absolute

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
async def metric_type(client):
    _now = lambda: datetime.now()
    _tags = {"name": "test"}
    type_name = Measurement(tags=_tags, timestamp=_now(), type="counter", value=1)
    yield type_name


async def test_put_metric(client, metric_type):
    assert metric_type.type == "counter"
    cw = cloudwatch_resource(client=client)
    cw.put_metric(metric_type)


async def test_put_alarm(client, metric_type, threshold=1):
    assert metric_type.type == "counter"
    cw = cloudwatch_resource(client=client)
    cw.put_alarm(metric_type, threshold)
