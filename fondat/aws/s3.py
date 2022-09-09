"""Fondat module for Amazon Simple Storage Service (S3)."""

import fondat.aws.client
import fondat.codec
import logging

from collections.abc import Iterable
from contextlib import asynccontextmanager
from fondat.aws.client import Config
from fondat.codec import Binary, String
from fondat.error import InternalServerError, NotFoundError
from fondat.pagination import Page
from fondat.resource import operation, resource
from fondat.security import Policy
from fondat.validation import validate_arguments
from typing import Any
from urllib.parse import quote


_logger = logging.getLogger(__name__)


@validate_arguments
def bucket_resource(
    bucket: str,
    *,
    prefix: str | None = None,
    suffix: str | None = None,
    key_type: type,
    value_type: type,
    compress: Any = None,
    encode_keys: bool = False,
    config: Config | None = None,
    policies: Iterable[Policy] | None = None,
):
    """
    Create S3 bucket resource.

    Parameters:
    • bucket: name of bucket to contain objects
    • prefix: prefix for all objects
    • suffix: suffix for all objects
    • key_type: type of key to identify object
    • value_type: type of value stored in each object
    • compress: algorithm to compress and decompress content
    • encode_keys: URL encode and decode object keys
    • config: client configuration
    • policies: security policies to apply to all operations
    """

    prefix = prefix or ""
    suffix = suffix or ""

    key_codec = fondat.codec.get_codec(String, key_type)
    value_codec = fondat.codec.get_codec(Binary, value_type)

    @asynccontextmanager
    async def create_client():
        async with fondat.aws.client.create_client("s3", config=config) as client:
            yield client

    @resource
    class Object:
        """S3 object resource."""

        def __init__(self, key: key_type):
            key = key_codec.encode(key)
            if encode_keys:
                key = quote(key, safe="")
            self._key = f"{prefix}{key}{suffix}"

        @operation(policies=policies)
        async def get(self) -> value_type:
            async with create_client() as client:
                try:
                    response = await client.get_object(Bucket=bucket, Key=self._key)
                    async with response["Body"] as stream:
                        body = await stream.read()
                    if compress:
                        body = compress.decompress(body)
                    return value_codec.decode(body)
                except client.exceptions.NoSuchKey:
                    raise NotFoundError
                except Exception as e:
                    _logger.error(e)
                    raise InternalServerError from e

        @operation(policies=policies)
        async def put(self, value: value_type) -> None:
            body = value_codec.encode(value)
            if compress:
                body = compress.compress(body)
            async with create_client() as client:
                try:
                    await client.put_object(Bucket=bucket, Key=self._key, Body=body)
                except Exception as e:
                    _logger.error(e)
                    raise InternalServerError from e

        @operation(policies=policies)
        async def delete(self) -> None:
            async with create_client() as client:
                try:
                    await client.delete_object(Bucket=bucket, Key=self._key)
                except Exception as e:
                    _logger.error(e)
                    raise InternalServerError from e

    @resource
    class Bucket:
        """S3 bucket resource."""

        @operation(policies=policies)
        async def get(
            self,
            limit: int | None = None,
            cursor: bytes | None = None,
        ) -> Page[str]:
            kwargs = {}
            if limit and limit > 0:
                kwargs["MaxKeys"] = limit
            if prefix:
                kwargs["Prefix"] = prefix
            if cursor is not None:
                kwargs["ContinuationToken"] = cursor.decode()
            async with create_client() as client:
                try:
                    response = await client.list_objects_v2(Bucket=bucket, **kwargs)
                    next_token = response.get("NextContinuationToken")
                    page = Page(
                        items=[
                            content["Key"][len(prefix) : len(content["Key"]) - len(suffix)]
                            for content in response.get("Contents", ())
                        ],
                        cursor=next_token.encode() if next_token else None,
                    )
                    return page
                except Exception as e:
                    _logger.error(e)
                    raise InternalServerError from e

        def __getitem__(self, key: key_type) -> Object:
            return Object(key)

    return Bucket()
