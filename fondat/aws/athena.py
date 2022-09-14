"""AWS Athena module."""

import asyncio
import fondat.codec
import fondat.sql
import re
import types
import typing

from collections import deque
from collections.abc import AsyncIterator, Iterable, Set
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from fondat.aws.client import create_client
from fondat.codec import DecodeError, EncodeError
from fondat.types import is_subclass, literal_values, split_annotated
from functools import cache
from types import NoneType
from typing import Any, Generic, TypedDict, TypeVar, is_typeddict
from uuid import UUID


Expression = fondat.sql.Expression
Param = fondat.sql.Param


T = TypeVar("T")


DEFAULT_PAGE_SIZE = 1000


@contextmanager
def _reraise(exception: Exception):
    try:
        yield
    except Exception as e:
        raise exception from e


class Codec(Generic[T]):
    """Base class for Athena codecs."""

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
        return str(value)

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
    @staticmethod
    def handles(python_type: T) -> bool:
        return (
            isinstance(python_type, types.UnionType)
            or typing.get_origin(python_type) is typing.Union
        )

    def __init__(self, python_type: Any):
        super().__init__(python_type)
        self.codecs = [get_codec(arg) for arg in typing.get_args(python_type)]

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
    @staticmethod
    def handles(python_type: T) -> bool:
        return typing.get_origin(python_type) is typing.Literal

    def __init__(self, python_type: Any):
        super().__init__(python_type)
        self.literals = literal_values(python_type)
        types = list({type(literal) for literal in self.literals})
        if len(types) != 1:
            raise TypeError("mixed-type literals not supported")
        self.codec = get_codec(types[0])

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
    Results of a statement execution.

    Parameters:
    • statement: statement that was executed
    • query_execution_id: identifies Athena query execution
    • page_size: number of rows to retrieve in each page request
    • result_type: the type in which to return each row result

    A valid result type can be one of:
    • dataclass: column names are object attributes
    • TypedDict: column names are dictionary keys
    • list[type]: columns are returned in the order queried
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
        self.codecs = None
        self.rows = deque()
        self.columns = None
        self.next_token = None

    def __aiter__(self):
        return self

    async def __anext__(self) -> T:

        while self.columns is None or (not self.rows and self.next_token):

            kwargs = {"QueryExecutionId": self.query_execution_id, "MaxResults": self.page_size}

            if self.next_token is not None:
                kwargs["NextToken"] = self.next_token

            async with create_client("athena") as client:
                response = await client.get_query_results(**kwargs)

            first_row = self.columns is None

            if self.columns is None:
                self.columns = [
                    column["Name"]
                    for column in response["ResultSet"]["ResultSetMetadata"]["ColumnInfo"]
                ]

            for result in response["ResultSet"]["Rows"]:
                row = [datum.get("VarCharValue") for datum in result["Data"]]
                if first_row:
                    first_row = False
                    if row == self.columns:
                        continue  # skip apparent header row
                self.rows.append(row)

            self.next_token = response.get("NextToken")

        if not self.rows:
            raise StopAsyncIteration

        if not self.codecs:
            if typing.get_origin(self.result_type) is list:
                codec = get_codec(typing.get_args(self.result_type)[0])
                self.codecs = [codec for n in range(len(self.columns))]
            else:
                hints = typing.get_type_hints(self.result_type, include_extras=True)
                self.codecs = [get_codec(hints[key]) for key in self.columns]

        row = self.rows.popleft()
        decoded = [self.codecs[n].decode(row[n]) for n in range(len(row))]

        if typing.get_origin(self.result_type) is list:
            return decoded

        d = {self.columns[n]: decoded[n] for n in range(len(self.columns))}

        return d if is_typeddict(self.result_type) else self.result_type(**d)


def expand_expression(expression: Expression) -> str:
    """Expand an expression into SQL query text."""
    text = []
    for fragment in expression:
        match fragment:
            case str():
                text.append(fragment)
            case Param():
                text.append(get_codec(fragment.type).encode(fragment.value))
            case _:
                raise ValueError(f"unexpected fragment: {fragment}")
    return "".join(text)


class Database:
    """
    Represents a database, a logical grouping of tables.

    Parameters and attributes:
    • name: name of the database
    • catalog: name of catalog where database is defined
    • workgroup: default workgroup to perform queries
    • output_location: default output location for query results
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
        statement: Expression | str,
        workgroup: str | None = None,
        output_location: str | None = None,
        page_size: int = DEFAULT_PAGE_SIZE,
        result_type: type[T] | None = None,
    ) -> Results[T] | None:
        """
        Execute a SQL statement, optionally returning a result object to iterate results.

        Parameters:
        • statement: SQL statement to execute
        • workgroup: workgroup to excute query, or use database default
        • output_location: output location for query results, or use database default
        • page_size: number of rows to retrieve in each request to Athena
        • result_type: the type in which to return each row result

        A valid result type can be one of:
        • dataclass: column names are object attributes
        • TypedDict: column names are dictionary keys
        • list[type]: columns are returned in the order queried
        """

        workgroup = workgroup or self.workgroup
        output_location = output_location or self.output_location
        query = statement if isinstance(statement, str) else expand_expression(statement)

        async with create_client("athena") as client:

            kwargs = {}
            kwargs["QueryString"] = query
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

    async def create(
        self,
        if_not_exists: bool = False,
        location: str | None = None,
        properties: dict[str, str] | None = None,
    ):
        """
        Create the database in the data catalog.

        Parameters:
        • if_not_exists: suppress error if database already exists
        • location: location where database files and metadata are stored
        • properties: custom metadata properties
        """
        stmt = Expression("CREATE DATABASE ")
        if if_not_exists:
            stmt += "IF NOT EXISTS "
        stmt += f"`{self.name}`"
        if location is not None:
            stmt += " LOCATION "
            stmt += Param(location)
        if properties:
            stmt += " WITH DBPROPERTIES ("
            stmt += Expression.join(
                [Expression(Param(k), "=", Param(v)) for k, v in properties.items()], ", "
            )
            stmt += ")"
        await self.execute(stmt)

    async def drop(self, if_exists: bool = False, cascade: bool = False):
        """
        Remove the database from the data catalog.

        Parameters:
        • if_exists: suppress error if database doesn't exist
        • cascade: force all tables to be dropped in database
        """
        stmt = Expression("DROP DATABASE ")
        if if_exists:
            stmt += "IF EXISTS "
        stmt += f"`{self.name}`"
        if cascade:
            stmt += " CASCADE"
        await self.execute(stmt)

    async def table_names(self) -> set[str]:
        """Return a set of table names in database."""
        return {
            row[0]
            async for row in await self.execute(
                Expression(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema = ",
                    Param(self.name),
                ),
                result_type=list[str],
            )
        }

    async def table(self, name) -> "Table":
        """
        Return table object representing the current definition of a table in the database.

        Parameters:
        • name: name of table
        """
        subst = {"real": "float", "varchar": "string", "varbinary": "binary"}
        async with create_client("athena") as client:
            columns = [
                Column(row[0], subst.get(row[1].lower(), row[1]))
                async for row in await self.execute(
                    Expression(
                        "SELECT column_name, data_type FROM information_schema.columns ",
                        "WHERE table_schema = ",
                        Param(self.name),
                        " AND table_name = ",
                        Param(name),
                        " ORDER BY ordinal_position",
                    ),
                    result_type=list[str],
                )
            ]
        return Table(database=self, name=name, columns=columns)


def athena_python_type(athena_type: str) -> Any:
    """Return a Python type compatible with the specified Athena type."""
    match re.fullmatch(r"([a-z]+).*").group(1):
        case "boolean":
            return bool
        case "tinyint" | "smallint" | "int" | "integer" | "bigint":
            return int
        case "double" | "float":
            return float
        case "decimal":
            return Decimal
        case "char" | "varchar" | "string":
            return str
        case "binary":
            return bytes
        case "date":
            return date
        case "timestamp":
            return datetime


@dataclass
class Column:
    """Represents a database column."""

    name: str
    athena_type: str
    python_type: Any = None

    def __str__(self):
        return f"`{self.name}` {self.athena_type}"

    def __post_init__(self):
        if self.python_type is None:
            self.python_type = athena_python_type(self.athena_type)


class Table:
    """
    Represents a table in a database.

    Parameters and attributes:
    • database: database where the table is managed
    • name: name of the table
    • columns: column definitions in table
    """

    def __init__(
        self,
        *,
        database: Database,
        name: str,
        columns: Iterable[Column],
    ):
        self.database = database
        self.name = name
        self.columns = columns

    def python_types(self, columns: Set[str] | None = None) -> dict[str, Any]:
        """
        Return Python types for database columns.

        Parameters:
        • columns: columns to return types, or None for all
        """
        if columns is None:
            columns = {column.name for column in self.columns}
        types = {c.name: c.python_type for c in self.columns if c.name in columns}
        if len(types) != len(columns):
            raise ValueError(f"unknown column(s): {', '.join(columns - types)}")
        return types

    async def create(
        self,
        *,
        external: bool = True,
        if_not_exists: bool = False,
        partitioned_by: Iterable[str | Column] | None = None,
        location: str,
        properties: dict[str, str] | None = None,
    ):
        """
        Create table in database.

        Parameters:
        • external: table is not a governed table or Iceberg table
        • if_not_exists: suppress error if table already exists
        • partitioned_by: partition columns
        • location: location where table files and metadata are stored
        • properties: custom metadata properties
        """
        stmt = Expression("CREATE ")
        if external:
            stmt += "EXTERNAL "
        stmt += "TABLE "
        if if_not_exists:
            stmt += "IF NOT EXISTS "
        stmt += f"`{self.name}` ("
        stmt += Expression.join([str(column) for column in self.columns], ", ")
        stmt += ")"
        if partitioned_by:
            stmt += " PARTITIONED BY ("
            stmt += Expression.join([str(p) for p in partitioned_by], ",")
            stmt += ")"
        stmt += f" LOCATION '{location}'"
        if properties:
            stmt += " TBLPROPERTIES ("
            stmt += Expression.join(
                [Expression(Param(k), "=", Param(v)) for k, v in properties.items()], ", "
            )
            stmt += ")"
        await self.database.execute(stmt)

    async def drop(
        self,
        *,
        if_exists: bool = False,
    ):
        """
        Drop table from database.

        Parameters:
        • if_exists: suppress error if table doesn't exist
        """
        stmt = Expression("DROP TABLE ")
        if if_exists:
            stmt += "IF EXISTS "
        stmt += f"`{self.name}`"
        await self.database.execute(stmt)

    async def select(
        self,
        *,
        columns: Set[str] | None = None,
        where: Expression | str | None = None,
        order_by: Expression | str | None = None,
        page_size: int = DEFAULT_PAGE_SIZE,
        offset: int | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Select rows from table.

        • columns: names of columns to select or None to select all columns
        • where: WHERE expression to select rows or None to select all
        • order_by: ORDER BY expression
        • page_size: number of rows to retrieve in each request to Athena
        • offset: number of rows to skip
        • limit: limit the number of rows returned
        """

        if not columns:
            columns = {c.name for c in self.columns}

        stmt = Expression("SELECT ")
        stmt += Expression.join([f'"{column}"' for column in columns], ", ")
        stmt += f' FROM "{self.name}"'
        if where:
            stmt += " WHERE "
            stmt += where
        if order_by:
            stmt += " ORDER BY "
            stmt += order_by
        if offset is not None:
            stmt += f" OFFSET {offset}"
        if limit is not None:
            stmt += f" LIMIT {limit}"

        return await self.database.execute(
            statement=stmt,
            page_size=page_size,
            result_type=TypedDict("Row", self.python_types(columns)),
        )

    async def insert(
        self,
        *,
        values: dict[str, Any],
    ):
        """
        Insert row into table.

        Parmeters:
        • values: column values to insert
        """

        types = self.python_types(values.keys())

        stmt = Expression(
            f'INSERT INTO "{self.name}" (',
            Expression.join([f'"{k}"' for k in values.keys()], ", "),
            ") VALUES (",
            Expression.join([Param(v, types[k]) for k, v in values.items()], ", "),
            ")",
        )

        await self.database.execute(stmt)

    async def update(self, *, values: dict[str, Any], where: Expression | None):
        """
        Update row(s) in table.

        Parmeters:
        • values: column values to update
        • where: WHERE expression to select rows to update or None to update all
        """

        if not values:
            return

        types = self.python_types(values.keys())

        stmt = Expression(
            f'UPDATE "{self.name}" SET ',
            Expression.join(
                [Expression(f'"{k}"=', Param(v, types[k])) for k, v in values.items()], ", "
            ),
        )
        if where:
            stmt += " WHERE "
            stmt += where

        await self.database.execute(stmt)

    async def delete(self, *, where: Expression | None):
        """
        Delete row(s) in table.

        Parmeters:
        • where: WHERE expression to select rows to delete or None to delete all
        """
        stmt = Expression(f'DELETE FROM "{self.name}"')
        if where:
            stmt += " WHERE "
            stmt += where
        await self.database.execute(stmt)
