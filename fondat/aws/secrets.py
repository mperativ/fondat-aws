"""Fondat module for AWS Secrets Manager."""

import logging

from collections.abc import Iterable
from contextlib import suppress
from fondat.aws import Service, wrap_client_error
from fondat.data import datacls
from fondat.error import NotFoundError
from fondat.http import AsBody, InBody
from fondat.memory import memory_resource
from fondat.resource import resource, operation
from fondat.security import Policy
from time import time
from typing import Annotated, Any, Union


_logger = logging.getLogger(__name__)


@datacls
class Secret:
    value: Union[str, bytes]


def secrets_resource(
    service: Service = None,
    cache_size: int = 0,
    cache_expire: Union[int, float] = 1,
    policies: Iterable[Policy] = None,
) -> Any:
    """
    Create secrets resource.

    Parameters:
    • service: AWS secretsmanager service object
    • cache: time in seconds to cache secrets
    • policies: security policies to apply to all operations
    """

    if service is None:
        service = Service("secretsmanager")

    if service.name != "secretsmanager":
        raise TypeError("expecting secretsmanager service object")

    cache = (
        memory_resource(
            key_type=str,
            value_type=Secret,
            size=cache_size,
            evict=True,
            expire=cache_expire,
        )
        if cache_size
        else None
    )

    @resource
    class SecretResource:
        """..."""

        __slots__ = ("name",)

        def __init__(self, name: str):
            self.name = name

        @operation(policies=policies)
        async def get(self, version_id: str = None, version_stage: str = None) -> Secret:
            """Get secret."""
            if cache:
                with suppress(NotFoundError):
                    return await cache[self.name].get()
            kwargs = {}
            kwargs["SecretId"] = self.name
            if version_id is not None:
                kwargs["VersionId"] = version_id
            if version_stage is not None:
                kwargs["VersionStage"] = version_stage
            client = await service.client()
            with wrap_client_error():
                value = await client.get_secret_value(**kwargs)
            secret = Secret(value=value.get("SecretString") or value.get("SecretBinary"))
            if cache:
                await cache[self.name].put(secret)
            return secret

        @operation(policies=policies)
        async def put(self, secret: Annotated[Secret, AsBody]):
            """Update secret."""
            args = {
                "SecretString"
                if isinstance(secret.value, str)
                else "SecretBinary": secret.value
            }
            client = await service.client()
            with wrap_client_error():
                await client.put_secret_value(SecretId=self.name, **args)
            if cache:
                await cache[self.name].put(secret)

        @operation(policies=policies)
        async def delete(self):
            """Delete secret."""
            if cache:
                with suppress(NotFoundError):
                    await cache[self.name].delete()
            client = await service.client()
            with wrap_client_error():
                await client.delete_secret(SecretId=self.name)

    @resource
    class SecretsResource:
        """..."""

        @operation(policies=policies)
        async def post(
            self,
            name: Annotated[str, InBody],
            secret: Annotated[Secret, InBody],
            kms_key_id: Annotated[str, InBody] = None,
            tags: Annotated[dict[str, str], InBody] = None,
        ):
            """Create secret."""
            kwargs = {}
            kwargs["Name"] = name
            if isinstance(secret.value, str):
                kwargs["SecretString"] = secret.value
            else:
                kwargs["SecretBinary"] = secret.value
            if kms_key_id is not None:
                kwargs["KmsKeyId"] = kms_key_id
            if tags is not None:
                kwargs["Tags"] = [{"Key": k, "Value": v} for k, v in tags.items()]
            client = await service.client()
            with wrap_client_error():
                await client.create_secret(**kwargs)
            if cache:
                await cache[name].put(secret)

        def __getitem__(self, name: str) -> SecretResource:
            return SecretResource(name)

    return SecretsResource()
