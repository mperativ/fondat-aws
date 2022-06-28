"""
Fondat AWS client module.
"""

import botocore.config
import fondat.error
import logging

from aiobotocore.client import AioBaseClient
from aiobotocore.session import AioSession
from botocore.exceptions import ClientError
from contextlib import asynccontextmanager, contextmanager
from fondat.data import datacls
from typing import Annotated


_logger = logging.getLogger(__name__)


@datacls
class Config:
    profile: Annotated[str | None, "name of the profile to use"]
    region_name: Annotated[str | None, "name of the region to connect to"]
    verify: Annotated[bool | str, "verify TLS certificates or path to CA cert bundle"] = True
    endpoint_url: Annotated[str | None, "URL to use for constructed client"]
    aws_access_key_id: Annotated[str | None, "access key ID"]
    aws_secret_access_key: Annotated[str | None, "secret access key"]
    aws_session_token: Annotated[str | None, "session token"]
    config: Annotated[botocore.config.Config | None, "advanced configuration options"]


@asynccontextmanager
async def create_client(
    service_name: str,
    *,
    api_version: str | None = None,
    config: Config | None = None,
) -> AioBaseClient:
    """
    Create an aiobotocore client.

    Parameters:
    • service_name: the name of the service to access
    • api_version: the API version to use  [latest]
    • config: session and client configuration

    If no configuration is provided, or configuration parameters are omitted, then
    aiobotocore will revert to searching environment variables and files in ~/.aws/.
    """

    session = AioSession(profile=config.profile if config else None)
    async with session.create_client(
        service_name=service_name,
        region_name=config.region_name if config else None,
        api_version=api_version,
        use_ssl=True,
        verify=config.verify if config else True,
        endpoint_url=config.endpoint.url if config else None,
        aws_access_key_id=config.aws_access_key_id if config else None,
        aws_secret_access_key=config.aws_secret_access_key if config else None,
        aws_session_token=config.aws_session_token if config else None,
        config=config.config if config else None,
    ) as client:
        yield client


@contextmanager
def wrap_client_error():
    """Catch any raised ClientError and reraise as a Fondat resource error."""
    try:
        yield
    except ClientError as ce:
        if ce.response["Error"]["Code"] == "ResourceNotFoundException":
            status = 404
        else:
            status = ce.response["ResponseMetadata"]["HTTPStatusCode"]
        raise fondat.error.errors[status] from ce
