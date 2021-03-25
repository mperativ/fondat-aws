import aiobotocore
import fondat.codec
import fondat.pagination
import logging

from collections.abc import Iterable
from fondat.aws import Client
from fondat.codec import Binary, String
from fondat.error import InternalServerError, NotFoundError
from fondat.resource import resource, operation, mutation
from fondat.security import SecurityRequirement
from typing import Any
from fondat.monitoring import Measurement, Counter, Gauge, Absolute


_logger = logging.getLogger(__name__)


def cloudwatch_resource(
    *,
    client: Client,
    security: Iterable[SecurityRequirement] = None,
):

    if client.service_name != "cloudwatch":
        raise TypeError("expecting cloudwatch client")

    @resource
    class Metric:
        @mutation(security=security)
        async def put_metric(self, measurement: Measurement):
            await client.put_metric_data(
                MetricData=[
                    {
                        "MetricName": measurement.tags["name"],
                        "Dimensions": [
                            {"Name": measurement.type, "Value": str(measurement.value)},
                        ],
                    },
                ],
                Namespace=measurement.type,
            )

        @mutation(security=security)
        async def put_alarm(self, measurement: Measurement, threshold: int):
            await client.put_metric_alarm(
                AlarmName=measurement.type + " Value",
                ComparisonOperator="GreaterThanThreshold",
                EvaluationPeriods=1,
                MetricName=measurement.tags["name"],
                Namespace=measurement.type,
                Period=60,
                Statistic="Average",
                Threshold=threshold,
                ActionsEnabled=False,
            )

    return Metric()
