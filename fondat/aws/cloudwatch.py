"""Fondat module for AWS CloudWatch."""

import asyncio
import logging

from collections import deque
from collections.abc import Iterable
from copy import copy
from datetime import datetime, timezone
from fondat.aws.client import Config, create_client
from fondat.codec import JSON, get_codec
from fondat.data import datacls
from fondat.http import AsBody
from fondat.monitor import Measurement, Monitor
from fondat.resource import operation, resource
from fondat.security import Policy
from fondat.validation import validate_arguments
from typing import Annotated, Any, Literal


_logger = logging.getLogger(__name__)


Unit = Literal[
    "Seconds",
    "Microseconds",
    "Milliseconds",
    "Bytes",
    "Kilobytes",
    "Megabytes",
    "Gigabytes",
    "Terabytes",
    "Bits",
    "Kilobits",
    "Megabits",
    "Gigabits",
    "Terabits",
    "Percent",
    "Count",
    "Bytes/Second",
    "Kilobytes/Second",
    "Megabytes/Second",
    "Gigabytes/Second",
    "Terabytes/Second",
    "Bits/Second",
    "Kilobits/Second",
    "Megabits/Second",
    "Gigabits/Second",
    "Terabits/Second",
    "Count/Second",
    "None",
]


unit_conversions = {
    "s": "Seconds",
    "μs": "Microseconds",
    "ms": "Milliseconds",
    "B": "bytes",
    "kB": "Kilobytes",
    "MB": "Megabytes",
    "GB": "Gigabytes",
    "TB": "Terabytes",
    "b": "Bits",
    "kb": "Kilobits",
    "Mb": "Megabits",
    "Gb": "Gigabits",
    "Tb": "Terabits",
    "%": "Percent",
    "B/s": "Bytes/Second",
    "kB/s": "Kilobytes/Second",
    "MB/s": "Megabytes/Second",
    "GB/s": "Gigabytes/Second",
    "TB/s": "Terabytes/Second",
    "b/s": "Bits/Second",
    "kb/s": "Kilobits/Second",
    "Mb/s": "Megabits/Second",
    "Gb/s": "Gigabits/Second",
    "TB/s": "Terabits/Second",
}


@datacls
class Dimension:
    name: str
    value: str


@datacls
class StatisticSet:
    sample_count: float
    sum: float
    minimum: float
    maximum: float


@datacls
class MetricDatum:
    metric_name: str
    dimensions: list[Dimension] | None
    timestamp: datetime | None
    value: float | None
    statistic_values: StatisticSet | None
    values: list[float] | None
    counts: list[float] | None
    unit: Unit | None
    storage_resolution: Literal[1, 60] | None


def _naming(value: Any) -> Any:
    match value:
        case dict():
            return {k.title().replace("_", ""): _naming(v) for k, v in value.items()}
        case list():
            return [_naming(i) for i in value]
        case _:
            return value


def _awsify(value: Any) -> dict[str, Any]:
    return _naming(get_codec(JSON, type(value)).encode(value))


def cloudwatch_resource(
    *,
    config: Config | None = None,
    policies: Iterable[Policy] | None = None,
):
    """
    Create CloudWatch resource.

    Parameters:
    • config: client configuration
    • policies: security policies to enforce for resource operations
    """

    @resource
    class NamespaceResource:
        """TODO."""

        def __init__(self, name: str):
            self.name = name

        @operation(policies=policies)
        async def post(
            self,
            metric_data: Annotated[list[MetricDatum], AsBody, "metrics data to post"],
        ):
            """Post metrics to namespace."""

            async with create_client("cloudwatch", config=config) as client:
                await client.put_metric_data(
                    Namespace=self.name,
                    MetricData=_awsify(metric_data),
                )

    @resource
    class CloudWatchResource:
        """Create CloudWatch resource."""

        def namespace(self, name: str) -> NamespaceResource:
            """TODO."""
            return NamespaceResource(name)

    return CloudWatchResource()


def _ascii(value: str) -> str:
    return value.encode("ASCII", "xmlcharrefreplace").decode("ASCII")


class CloudWatchMonitor(Monitor):
    """
    Monitor that publishes recorded measurements in AWS CloudWatch.

    Parameters:
    • namespace: TODO
    • storage_resolution: TODO
    • cache_size: TODO
    • config: TODO
    """

    @validate_arguments
    def __init__(
        self,
        namespace: str,
        *,
        storage_resolution: Literal[1, 60] = 60,
        cache_size: int = 100,
        config: Config | None = None,
    ):
        self.storage_resolution = storage_resolution
        self.cache_size = cache_size
        self._namespace_resource = cloudwatch_resource(config=config).namespace(namespace)
        self._measurements = []
        self._task = None

    def _round(self, timestamp: datetime) -> datetime:
        ts = int(timestamp.timestamp())  # truncate milliseconds
        ts -= ts % self.storage_resolution  # round to beginning of resolution interval
        return datetime.fromtimestamp(ts, tz=timezone.utc)

    async def _flush(self):
        measurements = deque()
        for measurement in self._measurements:
            measurement = copy(measurement)
            measurement.timestamp = self._round(measurement.timestamp)
            measurement.value = float(measurement.value)
            measurements.append(measurement)
        self._measurements = []  # prevent race between record and flush
        metric_data = []
        while measurements:
            m1 = measurements.popleft()
            datum = MetricDatum(
                metric_name=_ascii(m1.name),
                dimensions={_ascii(k): _ascii(v) for k, v in m1.tags.items()},
                timestamp=m1.timestamp,
                statistic_values=StatisticSet(
                    sample_count=1.0,
                    sum=m1.value,
                    minimum=m1.value,
                    maximum=m1.value,
                ),
                unit=unit_conversions.get(m1.unit) or "Counter"
                if m1.type == "counter"
                else None,
                storage_resolution=self.storage_resolution,
            )
            n = 0
            while n < len(measurements):
                m2 = measurements[n]
                if m2.name == m1.name and m2.tags == m1.tags and m2.timestamp == m1.timestamp:
                    statistic_values = datum.statistic_values
                    statistic_values.sample_count += 1.0
                    statistic_values.sum += m2.value
                    statistic_values.minimum = min(statistic_values.minimum, m2.value)
                    statistic_values.maximum = max(statistic_values.maximum, m2.value)
                    del measurements[n]
                else:
                    n += 1
            metric_data.append(datum)
            if len(metric_data) == 20 or not measurements:
                try:
                    await self._namespace_resource.post(metric_data=metric_data)
                except Exception as e:
                    _logger.exception("failure posting metric data")
                metric_data = []

    async def record(self, measurement: Measurement):
        """Record a measurement."""
        if len(measurement.tags) > 10:
            raise ValueError("measurement tags exceeds limit of 10")
        self._measurements.append(measurement)
        if len(self._measurements) >= self.cache_size:
            await self.flush(block=False)

    async def flush(self, block: bool = True):
        """Flush all recorded measurements."""
        if self._task and self._task.done():
            self._task = None
        if not self._task and self._measurements:
            self._task = asyncio.create_task(self._flush())
        if block and self._task:
            await self._task
