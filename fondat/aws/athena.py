"""..."""

import asyncio
import fondat.codec
import fondat.sql
import types
import typing

from collections import deque
from collections.abc import AsyncIterator, Iterable
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from fondat.aws.client import create_client
from fondat.codec import DecodeError, EncodeError
from fondat.types import is_subclass, split_annotated, literal_values
from functools import cache
from types import NoneType
from typing import Any, Generic, TypeVar, is_typeddict
from uuid import UUID


Expression = fondat.sql.Expression
Param = fondat.sql.Param


T = TypeVar("T")


@contextmanager
def _reraise(exception: Exception):
    try:
        yield
    except Exception as e:
        raise exception from e


class Codec(Generic[T]):
    """..."""

    def __init__(self, python_type: type[T]):
        self.python_type = python_type

    @staticmethod
    def handles(python_type: type) -> bool:
        """Return True if the codec handles the specified Python type."""
        raise NotImplementedError

    @staticmethod
    def encode(value: T) -> str:
        """Encode a Python value to a compatible Athena query expression."""
        raise NotImplementedError

    @staticmethod
    def decode(value: Any) -> T:
        """Decode a Athena result value to a compatible Python value."""
        raise NotImplementedError


class BoolCodec(Codec[bool]):
    @staticmethod
    def handles(python_type: Any) -> bool:
        return python_type is bool

    @staticmethod
    def encode(value: bool) -> str:
        return {True: "TRUE", False: "FALSE"}[value]

    @staticmethod
    def decode(value: Any) -> bool:
        with _reraise(DecodeError):
            return {"TRUE": True, "FALSE": False}[value.upper()]


class IntCodec(Codec[int]):
    @staticmethod
    def handles(python_type: Any) -> bool:
        return is_subclass(python_type, int) and not is_subclass(python_type, bool)

    @staticmethod
    def encode(value: int) -> str:
        return str(value)

    @staticmethod
    def decode(value: Any) -> int:
        if not isinstance(value, str):
            raise DecodeError
        with _reraise(DecodeError):
            return int(value)


class FloatCodec(Codec[float]):
    @staticmethod
    def handles(python_type: Any) -> bool:
        return is_subclass(python_type, float)

    def encode(self, value: float) -> str:
        return "DOUBLE '" + str(value) + "'"

    def decode(self, value: Any) -> float:
        if not isinstance(value, str):
            raise DecodeError
        with _reraise(DecodeError):
            return float(value)


class StrCodec(Codec):
    @staticmethod
    def handles(python_type: Any) -> bool:
        return python_type is str

    def encode(self, value: str) -> str:
        return "'" + value.replace("'", "''") + "'"

    def decode(self, value: Any) -> str:
        if not isinstance(value, str):
            raise DecodeError
        return value


class BytesCodec(Codec[bytes | bytearray]):
    @staticmethod
    def handles(python_type: Any) -> bool:
        return is_subclass(python_type, (bytes, bytearray))

    def encode(self, value: bytes | bytearray) -> str:
        with _reraise(EncodeError):
            return "X'" + value.hex() + "'"

    def decode(self, value: Any) -> bytes | bytearray:
        if not isinstance(value, str):
            raise DecodeError
        with _reraise(DecodeError):
            return bytes.fromhex(value)


class DecimalCodec(Codec[Decimal]):
    @staticmethod
    def handles(python_type: Any) -> bool:
        return is_subclass(python_type, Decimal)

    def encode(self, value: Decimal) -> str:
        return "DECIMAL '" + str(value) + "'"

    def decode(self, value: Any) -> Decimal:
        if not isinstance(value, str):
            raise DecodeError
        with _reraise(DecodeError):
            return Decimal(value)


class DateCodec(Codec[date]):
    @staticmethod
    def handles(python_type: Any) -> bool:
        return is_subclass(python_type, date) and not is_subclass(python_type, datetime)

    def encode(self, value: date) -> str:
        return "DATE '" + value.isoformat() + "'"

    def decode(self, value: Any) -> date:
        if not isinstance(value, str):
            raise DecodeError
        with _reraise(DecodeError):
            return date.fromisoformat(value)


class DatetimeCodec(Codec[datetime]):
    @staticmethod
    def handles(python_type: Any) -> bool:
        return is_subclass(python_type, datetime)

    def encode(self, value: datetime) -> str:
        if value.tzinfo is not None:  # doesn't support time zone yet
            raise EncodeError
        return "TIMESTAMP '" + value.isoformat(sep=" ", timespec="milliseconds") + "'"

    def decode(self, value: Any) -> datetime:
        if not isinstance(value, str):
            raise DecodeError
        return datetime.fromisoformat(value)


class UUIDCodec(Codec[UUID]):
    @staticmethod
    def handles(python_type: Any) -> bool:
        return is_subclass(python_type, UUID)

    def encode(self, value: UUID) -> str:
        return f"'{str(value)}'"

    def decode(self, value: Any) -> UUID:
        if not isinstance(value, str):
            raise DecodeError
        with _reraise(DecodeError):
            return UUID(value)


class NoneCodec(Codec[NoneType]):
    @staticmethod
    def handles(python_type: Any) -> bool:
        return python_type is NoneType

    def encode(self, value: NoneType) -> str:
        return "NULL"

    def decode(self, value: Any) -> NoneType:
        if value is not None:
            raise DecodeError
        return None


class UnionCodec(Codec[T]):
    def __init__(self, python_type: Any):
        super().__init__(python_type)
        self.codecs = [get_codec(arg) for arg in typing.get_args(python_type)]

    @staticmethod
    def handles(python_type: T) -> bool:
        return (
            isinstance(python_type, types.UnionType)
            or typing.get_origin(python_type) is typing.Union
        )

    def encode(self, value: T) -> str:
        for codec in self.codecs:
            if codec.handles(type(value)):
                with suppress(EncodeError):
                    return codec.encode(value)
        raise EncodeError

    def decode(self, value: Any) -> T:
        for codec in self.codecs:
            with suppress(DecodeError):
                return codec.decode(value)
        raise DecodeError


class LiteralCodec(Codec[T]):
    def __init__(self, python_type: Any):
        super().__init__(python_type)
        self.literals = literal_values(python_type)
        types = list({type(literal) for literal in self.literals})
        if len(types) != 1:
            raise TypeError("mixed-type literals not supported")
        self.codec = get_codec(types[0])

    @staticmethod
    def handles(python_type: T) -> bool:
        return typing.get_origin(python_type) is typing.Literal

    def encode(self, value: T) -> str:
        return self.codec.encode(value)

    def decode(self, value: Any) -> T:
        result = self.codec.decode(value)
        if result not in self.literals:
            raise DecodeError
        return result


@cache
def get_codec(python_type: type[T]) -> Codec[T]:
    """Return a codec compatible with the specified Python type."""

    python_type, _ = split_annotated(python_type)

    for codec_class in Codec.__subclasses__():
        if codec_class.handles(python_type):
            return codec_class(python_type)

    raise TypeError(f"no codec for {python_type}")


class Results(AsyncIterator[T]):
    """
    ...

    Parameters:
    • statement: ...
    • query_execution_id: ...
    • page_size: ...
    • result_type: ...
    """

    def __init__(
        self,
        statement: Expression,
        query_execution_id: str,
        page_size: int,
        result_type: type[T],
    ):
        self.statement = statement
        self.query_execution_id = query_execution_id
        self.page_size = page_size
        self.result_type = result_type
        self.codecs = {
            k: get_codec(t)
            for k, t in typing.get_type_hints(result_type, include_extras=True).items()
        }
        self.rows = deque()
        self.columns = None
        self.next_token = None

    def __aiter__(self):
        return self

    async def __anext__(self) -> T:

        while self.columns is None or (len(self.rows) == 0 and self.next_token):

            kwargs = {"QueryExecutionId": self.query_execution_id, "MaxResults": self.page_size}

            if self.next_token is not None:
                kwargs["NextToken"] = self.next_token

            async with create_client("athena") as client:
                response = await client.get_query_results(**kwargs)

            for result in response["ResultSet"]["Rows"]:
                row = [datum.get("VarCharValue") for datum in result["Data"]]
                if self.columns is None:
                    self.columns = row
                else:
                    self.rows.append(row)

            self.next_token = response.get("NextToken")

        if not self.rows:
            raise StopAsyncIteration

        row = self.rows.popleft()

        td = {
            self.columns[n]: self.codecs[self.columns[n]].decode(row[n])
            if row[n] is not None
            else None
            for n in range(len(self.columns))
        }

        return td if is_typeddict(self.result_type) else self.result_type(**td)


class Database:
    """
    ...

    Parameters and attributes:
    • name: ...
    • catalog: ...
    • workgroup: ...
    • output_location: ...
    """

    def __init__(
        self,
        *,
        name: str,
        catalog: str = "AwsDataCatalog",
        workgroup: str | None = None,
        output_location: str | None = None,
    ):
        self.name = name
        self.catalog = catalog
        self.workgroup = workgroup
        self.output_location = output_location

    async def execute(
        self,
        statement: Expression,
        workgroup: str | None = None,
        output_location: str | None = None,
        page_size: int = 1000,
        result_type: type[T] | None = None,
    ) -> Results[T] | None:
        """
        ...

        Parameters:
        • statement: ...
        • output_location: ...
        • workgroup: ...
        • page_size: ...
        • result_type: ...
        """

        workgroup = workgroup or self.workgroup
        output_location = output_location or self.output_location

        async with create_client("athena") as client:

            text = []
            for fragment in statement:
                match fragment:
                    case str():
                        text.append(fragment)
                    case Param():
                        text.append(get_codec(fragment.type).encode(fragment.value))
                    case _:
                        raise ValueError(f"unexpected fragment: {fragment}")

            kwargs = {}
            kwargs["QueryString"] = "".join(text)
            kwargs["QueryExecutionContext"] = {"Database": self.name, "Catalog": self.catalog}

            if output_location:
                kwargs["ResultConfiguration"] = {"OutputLocation": output_location}

            if workgroup:
                kwargs["WorkGroup"] = workgroup

            response = await client.start_query_execution(**kwargs)
            query_execution_id = response["QueryExecutionId"]

            state = "QUEUED"
            sleep = 0
            while state in {"QUEUED", "RUNNING"}:
                await asyncio.sleep(sleep)
                sleep = min((sleep * 2.0) or 0.1, 5.0)  # backout: 0.1 → 5 seconds
                query_execution = await client.get_query_execution(
                    QueryExecutionId=query_execution_id
                )
                state = query_execution["QueryExecution"]["Status"]["State"]

            if state != "SUCCEEDED":
                raise RuntimeError(query_execution)

            if result_type:
                return Results(statement, query_execution_id, page_size, result_type)
