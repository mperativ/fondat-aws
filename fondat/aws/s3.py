"""Fondat module for Amazon Simple Storage Service (S3)."""

import fondat.aws.client
import fondat.codec
import logging

from contextlib import asynccontextmanager
from fondat.codec import Binary, DecodeError, String, get_codec
from fondat.error import InternalServerError, NotFoundError
from fondat.pagination import Page
from fondat.resource import operation, resource
from typing import Any, Generic, TypeVar
from urllib.parse import quote


_logger = logging.getLogger(__name__)


@asynccontextmanager
async def create_client():
    async with fondat.aws.client.create_client("s3") as client:
        yield client


K = TypeVar("K")
V = TypeVar("V")


@resource
class BucketResource(Generic[K, V]):
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
        key_type: type[K] = str,
        value_type: type[V] = bytes,
        prefix: str = "",
        suffix: str = "",
        encode_keys: bool = False,
    ):
        self.name = name
        self.key_type = key_type
        self.value_type = value_type
        self.prefix = prefix
        self.suffix = suffix
        self.encode_keys = encode_keys

        self._key_codec = get_codec(String, key_type)
        self._value_codec = get_codec(Binary, value_type) if not issubclass(key_type, Stream) else None


    @operation
    async def get(self, limit: int | None = None, cursor: bytes | None = None) -> Page[K]:
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
                    key = self._key_codec.decode(key)
                except DecodeError:
                    continue  # ignore incompatible object keys
                items.append(key)
            next_token = response.get("NextContinuationToken")
            cursor = next_token.encode() if next_token is not None else None
            return Page(items=items, cursor=cursor)

    def __getitem__(self, key: K) -> "ObjectResource[K, V]":
        return ObjectResource(bucket=self, key=key)


@resource
class ObjectResource(Generic[K, V]):
    """
    S3 object resource.

    Parameters and attributes:
    • bucket: superodinate bucket resource
    • key: object key
    """

    def __init__(self, bucket: BucketResource[K, V], key: K):
        self.bucket = bucket
        self.key = key

    @property
    def _key(self) -> str:
        key = self.bucket._key_codec.encode(self.key)
        if self.bucket.encode_keys:
            key = quote(key, safe="")
        return f"{self.bucket.prefix}{key}{self.bucket.suffix}"

    @operation
    async def get(self) -> V:
        async with create_client() as client:
            try:
                response = await client.get_object(Bucket=self.bucket.name, Key=self._key)
                async with response["Body"] as stream:
                    body = await stream.read()
                return self.bucket._value_codec.decode(body)
            except client.exceptions.NoSuchKey:
                raise NotFoundError
            except Exception as e:
                _logger.error(e)
                raise InternalServerError from e

    @operation
    async def put(self, value: V) -> None:
        body = self.bucket._value_codec.encode(value)
        async with create_client() as client:
            try:
                await client.put_object(Bucket=self.bucket.name, Key=self._key, Body=body)
            except Exception as e:
                _logger.error(e)
                raise InternalServerError from e

    @operation
    async def delete(self) -> None:
        async with create_client() as client:
            try:
                await client.delete_object(Bucket=self.bucket.name, Key=self._key)
            except Exception as e:
                _logger.error(e)
                raise InternalServerError from e
