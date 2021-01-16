"""Fondat module for Amazon S3."""

import aiobotocore
import dataclasses
import logging

from collections.abc import Iterable
from urllib.parse import quote, unquote
from fondat.aws import Config
from fondat.codec import Binary, JSON, String, get_codec
from fondat.error import InternalServerError, NotFoundError
from fondat.paging import make_page_dataclass
from fondat.resource import resource, operation
from fondat.security import SecurityRequirement
from typing import Any, Optional


_logger = logging.getLogger(__name__)


def _asdict(config):
    return {k: v for k, v in dataclasses.asdict(config).items() if v is not None}


class Client:
    """
    S3 client class.

    Parameter:
    • config: AWS configuration object to override environment
    """

    def __init__(self, config: Config = None):
        self.config = config
        self.client = None

    async def open(self) -> None:
        """Open S3 client."""
        if self.client:
            raise RuntimeError("S3 client is already open")
        session = aiobotocore.get_session()
        client = session.create_client(
            "s3", **_asdict(self.config) if self.config else {}
        )
        self.client = await client.__aenter__()

    async def close(self) -> None:
        """Close S3 client."""
        if self.client:
            await self.client.__aexit__(None, None, None)
            self.client = None

    def __getattr__(self, name):
        if not self.client:
            raise RuntimeError("S3 client is not open")
        return getattr(self.client, name)

    async def __aenter__(self):
        await self.open()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()


def bucket_resource(
    *,
    client: Client,
    bucket: str,
    folder: str = None,
    key_type: type,
    value_type: type,
    extension: str = None,
    compress: Any = None,
    encode_keys: bool = False,
    security: Iterable[SecurityRequirement] = None,
):
    """
    Create S3 bucket resource.

    Parameters:
    • client: S3 client object
    • bucket: name of bucket to contain objects
    • folder: name of folder within bucket to contain objects
    • key_type: type of key to identify object
    • value_type: type of value stored in each object
    • extenson: filename extension to use for each file (including dot)
    • compress: algorithm to compress and decompress content
    • encode_keys: URL encode and decode object keys
    • security: security requirements to apply to all operations
    """

    key_codec = get_codec(String, key_type)
    value_codec = get_codec(Binary, value_type)

    @resource
    class Object:
        """S3 object resource."""

        def __init__(self, key: key_type):
            key = key_codec.encode(key)
            if encode_keys:
                key = quote(key, safe="")
            if extension is not None:
                key = f"{key}{extension}"
            if folder is not None:
                key = f"{folder}/{key}"
            self.key = key

        @operation(security=security)
        async def get(self) -> value_type:
            try:
                response = await client.get_object(Bucket=bucket, Key=self.key)
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

        @operation(security=security)
        async def put(self, value: value_type) -> None:
            body = value_codec.encode(value)
            if compress:
                body = compress.compress(body)
            try:
                await client.put_object(Bucket=bucket, Key=self.key, Body=body)
            except Exception as e:
                _logger.error(e)
                raise InternalServerError from e

        @operation(security=security)
        async def delete(self) -> None:
            try:
                await client.delete_object(Bucket=bucket, Key=self.key)
            except Exception as e:
                _logger.error(e)
                raise InternalServerError from e

    def _prefix(prefix):
        if not folder:
            return prefix
        if not prefix:
            return folder
        return f"{folder}/{prefix}"

    key_offset = len(folder) + 1 if folder else 0
    Page = make_page_dataclass("Page", str)

    @resource
    class Bucket:
        """S3 bucket resource."""

        async def get(
            self, prefix: str = None, limit: int = None, cursor: bytes = None
        ) -> Page:
            kwargs = {}
            if limit and limit > 0:
                kwargs["MaxKeys"] = limit
            if prefix := _prefix(prefix):
                kwargs["Prefix"] = prefix
            if cursor is not None:
                kwargs["ContinuationToken"] = cursor.decode()
            try:
                response = await client.list_objects_v2(Bucket=bucket, **kwargs)
                next_token = response.get("NextContinuationToken")
                page = Page(
                    items=[
                        content["Key"][key_offset:]
                        for content in response.get("Contents", ())
                    ],
                    cursor=next_token.encode() if next_token else None,
                    remaining=None,
                )
                return page
            except Exception as e:
                _logger.error(e)
                raise InternalServerError from e

        def __getitem__(self, key: key_type) -> Object:
            return Object(key)

    return Bucket()
