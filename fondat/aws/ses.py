"""Fondat module for Amazon Simple Email Service (SES)."""

import logging

from collections.abc import Iterable
from fondat.aws import Service, wrap_client_error
from fondat.http import AsBody
from fondat.resource import operation, resource, mutation
from fondat.security import Policy
from typing import Annotated, Union


_logger = logging.getLogger(__name__)


def ses_resource(
    service: Service = None,
    policies: Iterable[Policy] = None,
):
    """
    Create SES resource.

    Parameters:
    • service: SES service object
    • policies: security policies to apply to all operations
    """

    if service is None:
        service = Service("ses")

    if service.name != "ses":
        raise TypeError("expecting ses service object")

    @resource
    class Identity:
        """Verified identity."""

        def __init__(self, identity: str):
            self.identity = identity

        @operation(policies=policies)
        async def delete(self):
            """Delete the identity from verified identities."""
            client = await service.client()
            await client.delete_identity(Identity=self.identity)

    @resource
    class Identities:
        """Identities for Amazon SES account in a specific region."""

        @operation(policies=policies)
        async def post(self, identity):
            """Add email address to list of identities for SES account."""
            client = await service.client()
            await client.verify_email_identity(EmailAddress=identity)

        def __getitem__(self, identity) -> Identity:
            return Identity(identity)

    @resource
    class SESResource:
        """Simple Email Service (SES) resource."""

        @mutation(policies=policies)
        async def send_raw_email(
            self,
            source: str,
            destinations: Union[str, Iterable[str]],
            data: Annotated[bytes, AsBody],
        ):
            """
            Compose an email message and immediately queue it for sending.

            Parameters:
            • source: email address to send message message from
            • desinations: email address(es) to send message to
            • data: byte string containing headers and body of message to send
            """

            if isinstance(destinations, str):
                destinations = [destinations]

            client = await service.client()
            with wrap_client_error():
                await client.send_raw_email(
                    Source=source, Destinations=destinations, RawMessage={"Data": data}
                )

        identities = Identities()

    return SESResource()
