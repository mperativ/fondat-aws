"""AWS Athena module."""

import asyncio
import fondat.aws.client
import fondat.codec
import fondat.sql
import re
import types
import typing

from collections import deque
from collections.abc import AsyncGenerator, AsyncIterator, Iterable, Set
from contextlib import asynccontextmanager, contextmanager, suppress
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from fondat.resource import operation, query
from fondat.aws.client import create_client
from fondat.codec import Codec, DecodeError, EncodeError
from fondat.pagination import Page
from fondat.types import is_subclass, literal_values, strip_annotations
from types import NoneType
from typing import Annotated, Any, Literal, TypeVar
from uuid import UUID


Expression = fondat.sql.Expression
Param = fondat.sql.Param


PT = TypeVar("PT")  # Python type hint
AT = Any  # Athena type hint


@asynccontextmanager
async def create_client():
    async with fondat.aws.client.create_client("athena") as client:
        yield client


@contextmanager
def _reraise(exception: Exception):
    try:
        yield
    except Exception as e:
        raise exception from e


class AthenaCodec(Codec[PT, AT]):
    """Base class for Athena codecs."""

    _cache = {}


class BoolCodec(AthenaCodec[bool]):
    """..."""

    @staticmethod
    def handles(python_type: Any) -> bool:
        python_type = strip_annotations(python_type)
        return python_type is bool

    @staticmethod
    def encode(value: bool) -> AT:
        return {True: "TRUE", False: "FALSE"}[value]

    @staticmethod
    def decode(value: AT) -> bool:
        with _reraise(DecodeError):
            return {"TRUE": True, "FALSE": False}[value.upper()]


class IntCodec(AthenaCodec[int]):
    """..."""

    @staticmethod
    def handles(python_type: Any) -> bool:
        python_type = strip_annotations(python_type)
        return is_subclass(python_type, int) and not is_subclass(python_type, bool)

    @staticmethod
    def encode(value: int) -> AT:
        return str(value)

    @staticmethod
    def decode(value: AT) -> int:
        if not isinstance(value, str):
            raise DecodeError
        with _reraise(DecodeError):
            return int(value)


class FloatCodec(AthenaCodec[float]):
    """..."""

    @staticmethod
    def handles(python_type: Any) -> bool:
        python_type = strip_annotations(python_type)
        return is_subclass(python_type, float)

    def encode(self, value: float) -> AT:
        return str(value)

    def decode(self, value: AT) -> float:
        if not isinstance(value, str):
            raise DecodeError
        with _reraise(DecodeError):
            return float(value)


class StrCodec(AthenaCodec[str]):
    """..."""

    @staticmethod
    def handles(python_type: Any) -> bool:
        python_type = strip_annotations(python_type)
        return python_type is str

    def encode(self, value: str) -> AT:
        return "'" + value.replace("'", "''") + "'"

    def decode(self, value: AT) -> str:
        if not isinstance(value, str):
            raise DecodeError
        return value


class BytesCodec(AthenaCodec[bytes | bytearray]):
    """..."""

    @staticmethod
    def handles(python_type: Any) -> bool:
        python_type = strip_annotations(python_type)
        return is_subclass(python_type, (bytes, bytearray))

    def encode(self, value: bytes | bytearray) -> AT:
        with _reraise(EncodeError):
            return "X'" + value.hex() + "'"

    def decode(self, value: AT) -> bytes | bytearray:
        if not isinstance(value, str):
            raise DecodeError
        with _reraise(DecodeError):
            return bytes.fromhex(value)


class DecimalCodec(AthenaCodec[Decimal]):
    """..."""

    @staticmethod
    def handles(python_type: Any) -> bool:
        python_type = strip_annotations(python_type)
        return is_subclass(python_type, Decimal)

    def encode(self, value: Decimal) -> AT:
        return "DECIMAL '" + str(value) + "'"

    def decode(self, value: AT) -> Decimal:
        if not isinstance(value, str):
            raise DecodeError
        with _reraise(DecodeError):
            return Decimal(value)


class DateCodec(AthenaCodec[date]):
    """..."""

    @staticmethod
    def handles(python_type: Any) -> bool:
        python_type = strip_annotations(python_type)
        return is_subclass(python_type, date) and not is_subclass(python_type, datetime)

    def encode(self, value: date) -> AT:
        return "DATE '" + value.isoformat() + "'"

    def decode(self, value: AT) -> date:
        if not isinstance(value, str):
            raise DecodeError
        with _reraise(DecodeError):
            return date.fromisoformat(value)


class DatetimeCodec(AthenaCodec[datetime]):
    """..."""

    @staticmethod
    def handles(python_type: Any) -> bool:
        python_type = strip_annotations(python_type)
        return is_subclass(python_type, datetime)

    def encode(self, value: datetime) -> AT:
        if value.tzinfo is not None:  # doesn't support time zone yet
            raise EncodeError
        return "TIMESTAMP '" + value.isoformat(sep=" ", timespec="milliseconds") + "'"

    def decode(self, value: AT) -> datetime:
        if not isinstance(value, str):
            raise DecodeError
        return datetime.fromisoformat(value)


class UUIDCodec(AthenaCodec[UUID]):
    """..."""

    @staticmethod
    def handles(python_type: Any) -> bool:
        python_type = strip_annotations(python_type)
        return is_subclass(python_type, UUID)

    def encode(self, value: UUID) -> AT:
        return f"'{str(value)}'"

    def decode(self, value: AT) -> UUID:
        if not isinstance(value, str):
            raise DecodeError
        with _reraise(DecodeError):
            return UUID(value)


class NoneCodec(AthenaCodec[NoneType]):
    """..."""

    @staticmethod
    def handles(python_type: Any) -> bool:
        python_type = strip_annotations(python_type)
        return python_type is NoneType

    def encode(self, value: NoneType) -> AT:
        return "NULL"

    def decode(self, value: AT) -> NoneType:
        if value is not None:
            raise DecodeError
        return None


class UnionCodec(AthenaCodec[PT]):
    """..."""

    @staticmethod
    def handles(python_type: Any) -> bool:
        python_type = strip_annotations(python_type)
        origin = typing.get_origin(python_type) or python_type
        return origin in {types.UnionType, typing.Union}

    def __init__(self, python_type: Any):
        super().__init__(python_type)
        self.codecs = [AthenaCodec.get(arg) for arg in typing.get_args(python_type)]

    def encode(self, value: PT) -> AT:
        for codec in self.codecs:
            if codec.handles(type(value)):
                with suppress(EncodeError):
                    return codec.encode(value)
        raise EncodeError

    def decode(self, value: AT) -> PT:
        for codec in self.codecs:
            with suppress(DecodeError):
                return codec.decode(value)
        raise DecodeError


class LiteralCodec(AthenaCodec[PT]):
    """..."""

    @staticmethod
    def handles(python_type: Any) -> bool:
        python_type = strip_annotations(python_type)
        return typing.get_origin(python_type) is Literal

    def __init__(self, python_type: Any):
        super().__init__(python_type)
        self.literals = literal_values(python_type)
        types = list({type(literal) for literal in self.literals})
        if len(types) != 1:
            raise TypeError("mixed-type literals not supported")
        self.codec = AthenaCodec.get(types[0])

    def encode(self, value: PT) -> AT:
        return self.codec.encode(value)

    def decode(self, value: AT) -> PT:
        result = self.codec.decode(value)
        if result not in self.literals:
            raise DecodeError
        return result


class QueryExecutionResource:
    """Resource representing a query execution."""

    def __init__(self, id: str):
        self.id = id

    @operation
    async def get(self) -> dict[str, Any]:
        """Get query execution."""
        async with create_client() as client:
            response = await client.get_query_execution(QueryExecutionId=self.id)
            return response["QueryExecution"]

    @query
    async def results(
        self,
        limit: Annotated[int | None, "requested maximum rows to retrieve"] = None,
        cursor: Annotated[bytes | None, "cursor to continue pagination"] = None,
        decode: Annotated[bool, "decode column values"] = True,
    ) -> Page[dict[str, Any]]:
        """Get a page of results from a query execution."""
        kwargs = {"QueryExecutionId": self.id}
        if limit is not None:
            kwargs["MaxResults"] = limit
        if cursor is not None:
            kwargs["NextToken"] = cursor.decode()
        async with create_client() as client:
            response = await client.get_query_results(**kwargs)
        rows = [
            [datum.get("VarCharValue") for datum in row["Data"]]
            for row in response["ResultSet"]["Rows"]
        ]
        if not rows:
            return Page(items=[], cursor=None)
        names = [ci["Name"] for ci in response["ResultSet"]["ResultSetMetadata"]["ColumnInfo"]]
        if not cursor and rows[0] == names:
            del rows[0]  # skip apparent header
        next_token = response.get("NextToken")
        cursor = next_token.encode() if next_token else None
        codecs = (
            [
                AthenaCodec.get(athena_python_type(ci["Type"]))
                for ci in response["ResultSet"]["ResultSetMetadata"]["ColumnInfo"]
            ]
            if decode
            else None
        )
        return Page(
            items=[
                {
                    names[n]: codecs[n].decode(row[n]) if codecs else row[n]
                    for n in range(len(row))
                }
                for row in rows
            ],
            cursor=cursor,
        )


class QueryExecutionsResource:
    """Resource representing query executions."""

    @operation
    async def get(
        self,
        workgroup: str | None = None,
        limit: int | None = None,
        cursor: bytes | None = None,
    ) -> Page[str]:
        """List available query executions."""
        kwargs = {}
        if workgroup is not None:
            kwargs["WorkGroup"] = workgroup
        if limit is not None:
            kwargs["MaxResults"] = limit
        if cursor is not None:
            kwargs["NextToken"] = cursor.encode()
        async with create_client() as client:
            response = client.list_query_executions()
        next_token = response.get("NextToken")
        cursor = next_token.encode() if next_token else None
        return Page(items=response["QueryExecutionIds"], cursor=cursor)

    @operation
    async def post(
        self,
        database: Annotated[str, "name of database used in query execution"],
        catalog: Annotated[str, "name of catalog used in query execution"],
        query: Annotated[str, "SQL query statement to be executd"],
        output_location: Annotated[str | None, "location in S3 to store results"] = None,
        workgroup: Annotated[str | None, "name of workgroup in which query is started"] = None,
    ) -> Annotated[str, "query execution ID"]:
        """Start a query execution."""
        kwargs = {}
        kwargs["QueryString"] = query
        kwargs["QueryExecutionContext"] = {"Database": database, "Catalog": catalog}
        if output_location:
            kwargs["ResultConfiguration"] = {"OutputLocation": output_location}
        if workgroup:
            kwargs["WorkGroup"] = workgroup
        async with create_client() as client:
            response = await client.start_query_execution(**kwargs)
        return response["QueryExecutionId"]

    def __getitem__(self, id: Annotated[str, "query execution ID"]) -> QueryExecutionResource:
        return QueryExecutionResource(id)


class Results(AsyncIterator[dict[str, Any]]):
    """
    Paginates results of a statement execution.

    Parameters and attributes:
    • query_execution_id: identifies query for which to paginate results
    • decode: decode results using response metadata
    • page_size: number of rows to request in each page
    """

    _FIRST_PAGE = object()  # semaphore

    def __init__(
        self,
        query_execution_id: str,
        decode: bool,
        page_size: int,
    ):
        self.query_execution_resource = QueryExecutionResource(query_execution_id)
        self.decode = decode
        self.page_size = page_size
        self.rows = None
        self.cursor = Results._FIRST_PAGE

    def __aiter__(self):
        return self

    async def __anext__(self) -> dict[str, Any]:
        while not self.rows and self.cursor:
            page = await self.query_execution_resource.results(
                cursor=self.cursor if self.cursor is not Results._FIRST_PAGE else None,
                limit=self.page_size,
                decode=self.decode,
            )
            self.rows = deque(page.items)
            self.cursor = page.cursor
        if not self.rows:
            raise StopAsyncIteration
        return self.rows.popleft()


def expand_expression(expression: Expression) -> str:
    """Expand an expression into SQL text."""
    text = []
    for fragment in expression:
        match fragment:
            case str():
                text.append(fragment)
            case Param():
                text.append(AthenaCodec.get(fragment.type).encode(fragment.value))
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
        decode: bool = True,
        page_size: int = 1000,
        workgroup: str | None = None,
        output_location: str | None = None,
    ) -> Results:
        """
        Execute a SQL statement, returning an object to iterate any query results.

        Parameters:
        • statement: SQL statement to execute
        • decode: decode results using response metadata
        • page_size: number of rows to request in each page
        • workgroup: workgroup to excute query, or use database default
        • output_location: output location for query results, or use database default

        This method blocks until statement execution has completed. If an error occurs
        executing the statement, a RuntimeError is raised.
        """

        query_executions_resource = QueryExecutionsResource()

        query_execution_id = await query_executions_resource.post(
            database=self.name,
            catalog=self.catalog,
            query=statement if isinstance(statement, str) else expand_expression(statement),
            output_location=output_location or self.output_location,
            workgroup=workgroup or self.workgroup,
        )

        query_execution_resource = query_executions_resource[query_execution_id]

        state = "QUEUED"
        sleep = 0

        while state in {"QUEUED", "RUNNING"}:
            await asyncio.sleep(sleep)
            sleep = min((sleep * 2.0) or 0.1, 5.0)  # backout: 0.1 → 5 seconds
            result = await query_execution_resource.get()
            state = result["Status"]["State"]

        if state != "SUCCEEDED":
            raise RuntimeError(result["Status"]["AthenaError"]["ErrorMessage"])

        return Results(query_execution_id, decode, page_size)

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
            row["table_name"]
            async for row in await self.execute(
                Expression(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema = ",
                    Param(self.name),
                )
            )
        }

    async def table(self, name) -> "Table":
        """
        Return table object representing the current definition of a table in the database.

        Parameters:
        • name: name of table
        """
        subst = {"real": "float", "varchar": "string", "varbinary": "binary"}
        columns = [
            Column(row["column_name"], subst.get(row["data_type"].lower(), row["data_type"]))
            async for row in await self.execute(
                Expression(
                    "SELECT column_name, data_type FROM information_schema.columns ",
                    "WHERE table_schema = ",
                    Param(self.name),
                    " AND table_name = ",
                    Param(name),
                    " ORDER BY ordinal_position",
                ),
            )
        ]
        return Table(database=self, name=name, columns=columns)


_athena_type_pattern = re.compile(r"([a-z]+).*")


def athena_python_type(athena_type: str) -> Any:
    """Return a Python type compatible with the specified Athena type."""
    match _athena_type_pattern.fullmatch(athena_type).group(1):
        case "boolean":
            return bool | None
        case "tinyint" | "smallint" | "int" | "integer" | "bigint":
            return int | None
        case "double" | "float" | "real":
            return float | None
        case "decimal":
            return Decimal | None
        case "char" | "varchar" | "string" | "unknown":
            return str | None
        case "binary" | "varbinary":
            return bytes | None
        case "date":
            return date | None
        case "timestamp":
            return datetime | None
    raise ValueError(f"unrecognized Athena type: {athena_type}")


@dataclass
class Column:
    """A table column."""

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
    A database table.

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
        offset: int | None = None,
        limit: int | None = None,
        system_time: datetime | Expression | None = None,
        system_version: int | Expression | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Select rows from table.

        • columns: names of columns to select or None to select all columns
        • where: expression to select rows or None to select all
        • order_by: expression to order results
        • offset: number of rows to skip
        • limit: limit the number of rows returned
        • system_time: timestamp for time travel query
        • system_version: snapshot for time travel query
        """

        if not columns:
            columns = {column.name for column in self.columns}

        codecs = {column.name: AthenaCodec.get(column.python_type) for column in self.columns}

        if system_time and system_version:
            raise ValueError("can only specify one of system_time and system_version")

        if system_time and not isinstance(system_time, Expression):
            system_time = Param(system_time)

        if system_version and not isinstance(system_version, Expression):
            system_version = Param(system_version)

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
        if system_time is not None:
            stmt += Expression(" FOR SYSTEM_TIME AS OF ", system_time)
        if system_version is not None:
            stmt += Expression(" FOR SYSTEM_VERSION AS OF ", system_version)

        async for row in await self.database.execute(statement=stmt, decode=False):
            yield {key: codecs[key].decode(value) for key, value in row.items()}

    async def insert(
        self,
        *,
        row: dict[str, Any],
    ):
        """
        Insert row into table.

        Parmeters:
        • row: column key-value pairs to insert
        """

        types = self.python_types(row.keys())

        stmt = Expression(
            f'INSERT INTO "{self.name}" (',
            Expression.join([f'"{k}"' for k in row.keys()], ", "),
            ") VALUES (",
            Expression.join([Param(v, types[k]) for k, v in row.items()], ", "),
            ")",
        )

        await self.database.execute(stmt)

    async def update(self, *, row: dict[str, Any], where: Expression | None):
        """
        Update row(s) in table.

        Parmeters:
        • row: column key-value pairs to update
        • where: expression to select rows to update or None to update all
        """

        if not row:
            return

        types = self.python_types(row.keys())

        stmt = Expression(
            f'UPDATE "{self.name}" SET ',
            Expression.join(
                [Expression(f'"{k}"=', Param(v, types[k])) for k, v in row.items()], ", "
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
        • where: expression to select rows to delete or None to delete all
        """
        stmt = Expression(f'DELETE FROM "{self.name}"')
        if where:
            stmt += " WHERE "
            stmt += where
        await self.database.execute(stmt)
