"""Fondat module for Amazon Simple Storage Service (S3)."""

import fondat.aws.client
import fondat.codec
import logging

from contextlib import asynccontextmanager
from fondat.codec import BinaryCodec, DecodeError, StringCodec
from fondat.error import InternalServerError, NotFoundError
from fondat.pagination import Page
from fondat.resource import operation, resource
from fondat.types import is_subclass, strip_annotations
from typing import Any, Generic, TypeVar
from urllib.parse import quote


_logger = logging.getLogger(__name__)


@asynccontextmanager
async def create_client():
    async with fondat.aws.client.create_client("s3") as client:
        yield client


KT = TypeVar("KT")  # key type hint
VT = TypeVar("VT")  # value type hint


@resource
class BucketResource(Generic[KT, VT]):
    """
    S3 bucket resource.

    Parameters and attributes:
    • name: bucket name
    • key_type: type of key to identify object
    • value_type: type of value stored in each object
    • prefix: prefix for all objects
    • suffix: suffix for all objects
    • compress: algorithm to compress and decompress content
    • encode_keys: URL encode and decode object keys
    """

    def __init__(
        self,
        name: str,
        *,
        key_type: Any = str,
        value_type: Any = bytes,
        prefix: str = "",
        suffix: str = "",
        encode_keys: bool = False,
    ):
        self.name = name
        self.value_type = value_type
        self.prefix = prefix
        self.suffix = suffix
        self.encode_keys = encode_keys
        self.key_codec = StringCodec.get(key_type)


    @operation
    async def get(
        self,
        limit: int | None = None,
        cursor: bytes | None = None,
    ) -> Page[KT]:
        kwargs = {}
        if limit and limit > 0:
            kwargs["MaxKeys"] = limit
        if self.prefix:
            kwargs["Prefix"] = self.prefix
        if cursor is not None:
            kwargs["ContinuationToken"] = cursor.decode()
        async with create_client() as client:
            try:
                response = await client.list_objects_v2(Bucket=self.name, **kwargs)
            except Exception as e:
                _logger.error(e)
                raise InternalServerError from e
            items = []
            for content in response.get("Contents", ()):
                key = content["Key"]
                if not key.endswith(self.suffix):
                    continue  # ignore non-matching object keys
                key = key[len(self.prefix) : len(key) - len(self.suffix)]
                try:
                    key = self.key_codec.decode(key)
                except DecodeError:
                    continue  # ignore incompatible object keys
                items.append(key)
            next_token = response.get("NextContinuationToken")
            cursor = next_token.encode() if next_token is not None else None
            return Page(items=items, cursor=cursor)

    def __getitem__(self, key: KT) -> "ObjectResource[VT]":
        key = self.key_codec.encode(key)
        if self.encode_keys:
            key = quote(key, safe="")
        return ObjectResource(
            bucket=self.name,
            key=f"{self.prefix}{key}{self.suffix}",
            type=self.value_type
        )


@resource
class ObjectResource(Generic[VT]):
    """
    S3 object resource.

    Parameters and attributes:
    • bucket: superodinate bucket resource
    • key: object key
    """

    def __init__(
        self,
        bucket: str,
        key: str,
        type: Any,
    ):
        self.bucket = bucket
        self.key = key
        self.type = strip_annotations(type)
        self.codec = BinaryCodec.get(type)

    @operation
    async def get(self) -> VT:
        async with create_client() as client:
            try:
                response = await client.get_object(Bucket=self.bucket, Key=self.key)
                async with response["Body"] as stream:
                    body = await stream.read()
                return self.codec.decode(body)
            except client.exceptions.NoSuchKey:
                raise NotFoundError
            except Exception as e:
                _logger.error(e)
                raise InternalServerError from e

    @operation
    async def put(self, value: VT) -> None:
        body = self.codec.encode(value)
        async with create_client() as client:
            try:
                await client.put_object(Bucket=self.bucket, Key=self.key, Body=body)
            except Exception as e:
                _logger.error(e)
                raise InternalServerError from e

    @operation
    async def delete(self) -> None:
        async with create_client() as client:
            try:
                await client.delete_object(Bucket=self.bucket, Key=self.key)
            except Exception as e:
                _logger.error(e)
                raise InternalServerError from e
