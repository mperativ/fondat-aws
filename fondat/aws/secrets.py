"""Fondat module for AWS Secrets Manager."""

import fondat.aws.client
import logging

from collections.abc import Iterable
from contextlib import asynccontextmanager, suppress
from fondat.aws.client import Config, wrap_client_error
from fondat.data import datacls
from fondat.error import NotFoundError
from fondat.http import AsBody, InBody
from fondat.memory import memory_resource
from fondat.resource import operation, resource
from fondat.security import Policy
from typing import Annotated, Any


_logger = logging.getLogger(__name__)


@datacls
class Secret:
    value: str | bytes


def secrets_resource(
    cache_size: int = 0,
    cache_expire: int | float = 1,
    config: Config | None = None,
    policies: Iterable[Policy] | None = None,
) -> Any:
    """
    Create secrets resource.

    Parameters:
    • cache: time in seconds to cache secrets
    • config: client configuration
    • policies: security policies to apply to all operations
    """

    @asynccontextmanager
    async def create_client():
        async with fondat.aws.client.create_client("secretsmanager", config=config) as client:
            yield client

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
        async def get(
            self,
            version_id: str | None = None,
            version_stage: str | None = None,
        ) -> Secret:
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
            async with create_client() as client:
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
            async with create_client() as client:
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
            async with create_client() as client:
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
            kms_key_id: Annotated[str | None, InBody] = None,
            tags: Annotated[dict[str, str] | None, InBody] = None,
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
            async with create_client() as client:
                with wrap_client_error():
                    await client.create_secret(**kwargs)
                if cache:
                    await cache[name].put(secret)

        def __getitem__(self, name: str) -> SecretResource:
            return SecretResource(name)

    return SecretsResource()
