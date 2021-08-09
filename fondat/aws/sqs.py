"""Fondat module for Amazon Simple Queue Service (SQS)."""

import logging

from collections.abc import Iterable
from fondat.aws import Service
from fondat.codec import String, get_codec
from fondat.error import InternalServerError
from fondat.resource import resource, mutation
from fondat.security import Policy
from typing import Annotated, Optional


_logger = logging.getLogger(__name__)


def queue_resource(
    *,
    service: Service = None,
    queue_url: str,
    message_type: type,
    policies: Iterable[Policy] = None,
):
    """
    Create SQS queue resource.

    Parameters:
    • service: S3 service object
    • queue_url: the URL of the SQS queue
    • message_type: type of value transmitted in each message
    • security: security policies to apply to all operations
    """

    if service is None:
        service = Service("sqs")

    if service.name != "sqs":
        raise TypeError("expecting sqs service object")

    codec = get_codec(String, message_type)

    @resource
    class Queue:
        """SQS queue resource."""

        @mutation(policies=policies)
        async def send(self, message: message_type) -> None:
            """Send a message to the queue."""
            client = await service.client()
            try:
                await client.send_message(QueueUrl=queue_url, MessageBody=codec.encode(message))
            except Exception as e:
                _logger.error(e)
                raise InternalServerError from e

        @mutation(policies=policies)
        async def receive(
            self,
            wait_time_seconds: Annotated[int, "number of seconds to wait for a message"] = 0,
        ) -> Optional[message_type]:
            """Return the next message from the queue."""
            client = await service.client()
            response = await client.receive_message(
                QueueUrl=queue_url, WaitTimeSeconds=wait_time_seconds
            )
            if "Messages" not in response:
                return None
            try:
                result = codec.decode(response["Messages"][0]["Body"])
            except Exception as e:
                _logger.error(e)
                raise InternalServerError from e
            return result

    return Queue()
