import aiobotocore
import fondat.codec
import fondat.pagination
import logging

from collections.abc import Iterable
from fondat.aws import Client
from fondat.codec import Binary, String
from fondat.error import InternalServerError, NotFoundError
from fondat.resource import resource, operation
from fondat.security import SecurityRequirement
from typing import Any
from fondat.monitoring import Counter, Gauge, Absolute


_logger = logging.getLogger(__name__)


def cloudwatch_resource(
    *,
    client: Client,
    message_type: type,
    security: Iterable[SecurityRequirement] = None,
):

    if client.service_name != "cloudwatch":
        raise TypeError("expecting cloudwatch client")

    @cloudwatch_resource
    class Metric:
        @operation(security=security)
        async def put_metric(self, measurement: Measurement):
            response = client.put_metric_data(
                MetricData=[
                    {
                        "MetricName": measurement.type,
                        "Dimensions": [
                            {"Name": measurement.type, "Value": measurement.value},
                        ],
                    },
                ],
                Namespace=measurement,
            )

            return response

        @cloudwatch_resource
        async def put_alarm(self, measurement: Measurement):
            response = client.put_metric_alarm(
                AlarmName=measurement.type + " Value",
                ComparisonOperator="GreaterThanThreshold",
                EvaluationPeriods=1,
                MetricName=measurement.type,
                Namespace=measurement.type,
                Period=60,
                Statistic="Average",
                Threshold=70.0,
                ActionsEnabled=False,
            )

            return response
