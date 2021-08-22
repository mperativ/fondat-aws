"""Fondat package for Amazon Web Services."""

import fondat.error
import logging

from aiobotocore.client import AioBaseClient
from aiobotocore.session import get_session
from asyncio import get_running_loop
from contextlib import contextmanager, suppress
from botocore.exceptions import ClientError
from dataclasses import asdict
from fondat.data import datacls
from typing import Annotated, Any, Optional


_logger = logging.getLogger(__name__)


@datacls
class Config:
    aws_access_key_id: Annotated[Optional[str], "AWS access key ID"]
    aws_secret_access_key: Annotated[Optional[str], "AWS secret access key"]
    aws_session_token: Annotated[Optional[str], "AWS temporary session token"]
    endpoint_url: Annotated[Optional[str], "URL to use for constructed client"]
    profile_name: Annotated[Optional[str], "name of the AWS profile to use"]
    region_name: Annotated[Optional[str], "region to use when creating connections"]
    verify: Annotated[Optional[bool], "verify TLS certificates"]


def _kwargs(config: Config) -> dict[str, Any]:
    return {k: v for k, v in (asdict(config) if config else {}).items() if v is not None}


class Service:
    """
    Fondat AWS service object.

    Parameters:
    • name: the name of a service (example: "s3")
    • config: configuration object to initialize client

    If no configuration is specified, then the AWS client will use configuration and
    credentials in environment variables and/or files as consumed by Python AWS libraries and
    the AWS command line interface. For more information see:
    https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html.
    """

    def __init__(self, name: str, config: Config = None):
        self.name = name
        self.config = config
        self._client = None
        self._loop = None

    async def client(self) -> AioBaseClient:
        if self._client is None or self._loop is not get_running_loop():
            await self.close()
            _logger.debug(f"Creating new {self.name} client")
            session = get_session()
            client = session.create_client(service_name=self.name, **_kwargs(self.config))
            self._client = await client.__aenter__()
            self._loop = get_running_loop()
        return self._client

    async def close(self) -> None:
        """Release any resources associated with the service."""
        if self._client is not None:
            with suppress():
                await self._client.__aexit__(None, None, None)
        self._client = None


@contextmanager
def wrap_client_error():
    """Catch any raised ClientError and reraise as a Fondat resource error."""
    try:
        yield
    except ClientError as ce:
        status = ce.response["ResponseMetadata"]["HTTPStatusCode"]
        message = ce.response["Error"]["Message"]
        raise fondat.error.errors[status](message)
