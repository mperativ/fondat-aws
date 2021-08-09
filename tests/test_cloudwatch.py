import pytest

from datetime import datetime, timezone
from fondat.aws import Config, Service
import fondat.aws.cloudwatch as cw
from fondat.aws.cloudwatch import CloudWatchMonitor
from fondat.error import NotFoundError
from fondat.monitoring import Measurement, Counter, Gauge, Absolute
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
    service = Service(name="cloudwatch", config=config)
    yield service
    await service.close()


@pytest.fixture(scope="function")
async def metric_type():
    metric = cw.Metric(
        name="operation_requests_per_second",
        dimensions={"tenant_id": str(uuid4())},
        value=1234,
        timestamp=datetime.now(tz=timezone.utc),
        unit="Count",
    )
    yield metric


@pytest.fixture(scope="function")
async def measurement_counter():
    _now = lambda: datetime.now(tz=timezone.utc)
    _tags = {"name": "test"}
    measurement = Measurement(tags=_tags, timestamp=_now(), type="counter", value=1)
    yield measurement


@pytest.fixture(scope="function")
async def measurement_absolute():
    _now = lambda: datetime.now(tz=timezone.utc)
    _tags = {"name": "test"}
    measurement = Measurement(tags=_tags, timestamp=_now(), type="absolute", value=1)
    yield measurement


@pytest.fixture(scope="function")
async def measurement_gauge():
    _now = lambda: datetime.now(tz=timezone.utc)
    _tags = {"name": "test"}
    measurement = Measurement(tags=_tags, timestamp=_now(), type="gauge", value=1)
    yield measurement


@pytest.fixture(scope="function")
async def measurement_gauge_1():
    _now = lambda: datetime.now(tz=timezone.utc)
    _tags = {"name": "test"}
    measurement = Measurement(tags=_tags, timestamp=_now(), type="gauge", value=2)
    yield measurement


async def test_put_metric(service, metric_type):
    resource = cw.cloudwatch_resource(service=service).namespace("Mperativ/Tripper")
    await resource.post(metrics=[metric_type])


async def test_put_counter(service, measurement_counter):
    cwm = CloudWatchMonitor(service=service, namespace="Mperativ/Tripper")
    await cwm.record(measurement_counter)


async def test_put_absolute(service, measurement_absolute):
    cwm = CloudWatchMonitor(service=service, namespace="Mperativ/Tripper")
    await cwm.record(measurement_absolute)


async def test_put_gauge(service, measurement_gauge, measurement_gauge_1):
    cwm = CloudWatchMonitor(service=service, namespace="Mperativ/Tripper")
    await cwm.record(measurement_gauge)
    await cwm.record(measurement_gauge_1)
