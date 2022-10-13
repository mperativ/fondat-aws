"""Fondat module for Amazon Simple Storage Service (S3)."""

import fondat.aws.client
import fondat.codec
import fondat.error
import logging

from contextlib import asynccontextmanager, contextmanager, suppress
from fondat.codec import BinaryCodec, DecodeError, StringCodec
from fondat.error import InternalServerError, NotFoundError
from fondat.pagination import Page
from fondat.resource import operation, resource
from fondat.stream import Reader, Stream
from fondat.types import strip_annotations
from fondat.validation import MinValue, validate_arguments
from typing import Annotated, Any, Generic, TypeVar
from urllib.parse import quote


_logger = logging.getLogger(__name__)


KT = TypeVar("KT")  # key type hint
VT = TypeVar("VT")  # value type hint


@asynccontextmanager
async def create_client():
    async with fondat.aws.client.create_client("s3") as client:
        yield client


@contextmanager
def _log_wrap():
    try:
        yield
    except Exception as e:
        _logger.error(e)
        raise InternalServerError from e


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
            with _log_wrap():
                response = await client.list_objects_v2(Bucket=self.name, **kwargs)
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
            bucket=self.name, key=f"{self.prefix}{key}{self.suffix}", type=self.value_type
        )


CHUNK_SIZE = 5 * 1024 * 1024  # 5 MiB


@resource
class ObjectResource(Generic[VT]):
    """
    S3 object resource.

    Parameters and attributes:
    • bucket: name of bucket where object resides
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
        self.codec = BinaryCodec.get(type) if self.type is not Stream else None

    @operation
    async def get(self) -> VT:
        try:
            stream = await ObjectStream.new(self.bucket, self.key)
            if self.type is Stream:
                return stream
            async with stream:
                return self.codec.decode(await Reader(stream).read())
        except fondat.error.Error:
            raise
        except Exception as e:
            _logger.error(e)
            raise InternalServerError from e

    async def _basic_upload(self, value: VT) -> bool:
        with _log_wrap():
            if self.type is Stream:
                if not value.content_length or value.content_length > CHUNK_SIZE:
                    return False
                async with value as stream:  # automatically close
                    body = await Reader(stream).read()
            else:
                body = self.codec.encode(value)
            async with create_client() as client:
                await client.put_object(Bucket=self.bucket, Key=self.key, Body=body)
        return True

    async def _multipart_upload(self, value: VT):
        upload_id = None
        try:
            async with create_client() as client:
                async with Reader(value) as reader:  # automatically close
                    mpu = await client.create_multipart_upload(
                        Bucket=self.bucket,
                        Key=self.key,
                    )
                    upload_id = mpu["UploadId"]
                    etags = []
                    while chunk := await reader.read(CHUNK_SIZE):
                        part = await client.upload_part(
                            Bucket=self.bucket,
                            Key=self.key,
                            UploadId=upload_id,
                            PartNumber=len(etags) + 1,
                            Body=chunk,
                            ContentLength=len(chunk),
                        )
                        etags.append(part["ETag"])
                    await client.complete_multipart_upload(
                        Bucket=self.bucket,
                        Key=self.key,
                        UploadId=upload_id,
                        MultipartUpload={
                            "Parts": [
                                {
                                    "PartNumber": n + 1,
                                    "ETag": etags[n],
                                }
                                for n in range(len(etags))
                            ]
                        },
                    )
        except Exception as e:
            if upload_id:  # attempt to about upload if created
                with suppress(Exception):
                    await client.abort_multipart_upload(
                        Bucket=self.bucket,
                        Key=self.key,
                        UploadId=upload_id,
                    )
            _logger.error(e)
            raise InternalServerError from e

    @operation
    async def put(self, value: VT) -> None:
        if not await self._basic_upload(value):
            await self._multipart_upload(value)

    @operation
    async def delete(self) -> None:
        async with create_client() as client:
            with _log_wrap():
                await client.delete_object(Bucket=self.bucket, Key=self.key)


class ObjectStream(Stream):
    """Open an object to be read as a stream."""

    def __init__(self):
        raise TypeError("create using 'new' asynchronous class method")

    @classmethod
    async def new(cls, bucket: str, key: str) -> "ObjectStream":
        """
        Create a new object stream object.

        Parameters:
        • bucket: name of bucket where object resides
        • key: object key
        """
        self = ObjectStream.__new__(ObjectStream)
        self._context = create_client()
        client = await self._context.__aenter__()
        try:
            try:
                response = await client.get_object(Bucket=bucket, Key=key)
            except client.exceptions.NoSuchKey:
                raise NotFoundError
            except Exception as e:
                _logger.error(e)
                raise InternalServerError from e
        except:
            with suppress(Exception):
                await self.close()
            raise
        Stream.__init__(
            self, content_type=response["ContentType"], content_length=response["ContentLength"]
        )
        self._body = response["Body"]
        return self

    async def __anext__(self) -> bytes:
        if self._context:
            if chunk := await self._body.read(CHUNK_SIZE):
                return chunk
        raise StopAsyncIteration

    async def close(self):
        if self._context:
            await self._context.__aexit__(None, None, None)
            self._context = None
