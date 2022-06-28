from datetime import datetime, timezone
from fondat.aws.cloudwatch import (
    CloudWatchMonitor,
    Dimension,
    MetricDatum,
    StatisticSet,
    cloudwatch_resource,
)
from fondat.monitor import Measurement
from pytest import fixture


_now = lambda: datetime.now(tz=timezone.utc)


NAMESPACE = "Fondat/Test"


@fixture(scope="module")
def namespace_resource():
    return cloudwatch_resource().namespace(NAMESPACE)


async def test_put_metric_value(namespace_resource):
    await namespace_resource.post(
        metric_data=[
            MetricDatum(
                metric_name="test_put_metric_value",
                dimensions=[Dimension(name="foo", value="bar")],
                timestamp=_now(),
                value=1.23,
                unit="Kilobytes",
                storage_resolution=60,
            )
        ]
    )


async def test_put_metric_values(namespace_resource):
    await namespace_resource.post(
        metric_data=[
            MetricDatum(
                metric_name="test_put_metric_values",
                timestamp=_now(),
                values=[2.34, 3.45],
                counts=[2.0, 4.0],
                unit="Bytes",
                storage_resolution=1,
            )
        ]
    )


async def test_put_metric_statistics(namespace_resource):
    await namespace_resource.post(
        metric_data=[
            MetricDatum(
                metric_name="test_put_metric_values",
                timestamp=_now(),
                statistic_values=StatisticSet(
                    sample_count=123.0,
                    sum=63.733388507698265,
                    minimum=0.02425279885047038,
                    maximum=0.9989390658635393,
                ),
                unit="Bytes/Second",
                storage_resolution=60,
            )
        ]
    )


async def test_monitor():
    monitor = CloudWatchMonitor(namespace=NAMESPACE, storage_resolution=60)
    for n in range(10):
        await monitor.record(
            Measurement(
                name="test_monitor",
                tags={"a": "b"},
                type="gauge",
                value=n,
                unit="MB/s",
            )
        )
    await monitor.flush()
