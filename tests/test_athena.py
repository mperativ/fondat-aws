import asyncio
import fondat.aws.athena as athena
import random
import string

from datetime import date, datetime
from decimal import Decimal
from fondat.aws.athena import Column, Expression, Param, Table
from fondat.types import literal_values
from pytest import fixture
from types import NoneType
from typing import Literal
from uuid import UUID


@fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@fixture(scope="module")
async def database():
    name = "db-" + "".join(random.choices(string.ascii_lowercase, k=8))
    db = athena.Database(name=name, workgroup="primary")
    await db.create()
    yield db
    await db.drop(cascade=True)


async def _test_values(type, *values):
    codec = athena.AthenaCodec.get(type)
    db = athena.Database(name="foo", workgroup="primary")
    stmt = Expression("SELECT ")
    v = []
    for n in range(len(values)):
        v.append(Expression(Param(values[n], type), f" AS v{n}"))
    stmt += Expression.join(v, ", ")
    async for row in await db.execute(stmt, decode=True):
        for n in range(len(values)):
            assert row[f"v{n}"] == values[n]


async def test_str():
    await _test_values(str, "a", "b'c", "d''e")


async def test_bytes():
    await _test_values(bytes, b"\x01\x02\x03", b"hello", "world".encode())


async def test_boolean():
    await _test_values(bool, True, False)


async def test_int():
    await _test_values(int, 1, 2, 3)


async def test_float():
    await _test_values(float, 0.3, 1.1, 2.2, 3.3)


async def test_decimal():
    await _test_values(Decimal, Decimal("0.3"), Decimal("1.1111111111"))


async def test_date():
    await _test_values(date, date(2022, 9, 8), date.fromisoformat("2022-09-09"))


async def test_datetime():
    await _test_values(
        datetime,
        datetime(2022, 9, 8, 1, 2, 3, 456000),
        datetime.fromisoformat("2022-01-02T03:04:05.678"),
    )


async def test_none():
    await _test_values(NoneType, None)


async def test_union():
    UT = str | None
    await _test_values(UT, "a", None)


async def test_literal():
    L = Literal["a", "b", "c"]
    await _test_values(L, *literal_values(L))


async def test_uuid(database):
    value = UUID("2093f88a-99ab-4807-87f7-ab3997a199b5")
    stmt = Expression("SELECT ", Param(value), " AS value")
    async for row in await database.execute(stmt, decode=True):
        assert athena.AthenaCodec.get(UUID).decode(row["value"]) == value


async def test_crud(database):

    table = Table(
        database=database,
        name="foo",
        columns=[
            Column("id", "string", UUID),
            Column("binary", "binary", bytes),
            Column("boolean", "boolean", bool),
            Column("date", "date", date),
            Column("decimal", "decimal(8,2)", Decimal),
            Column("double", "double", float),
            Column("bigint", "bigint", int),
            Column("string", "string", str),
            Column("timestamp", "timestamp", datetime),
        ],
    )

    await table.create(
        external=False,
        location=f"s3://fondat/lake1/{database.name}/foo/",
        properties={"table_type": "ICEBERG"},
    )

    tables = await database.table_names()
    assert tables == {"foo"}

    row = {
        "id": UUID("b48ec27e-ce14-4eaf-9157-2ae4171a5218"),
        "binary": b"1234",
        "boolean": True,
        "date": date(2022, 9, 12),
        "decimal": Decimal("123456.78"),
        "double": 123.4567890,
        "bigint": 12345,
        "string": "string",
        "timestamp": datetime(2021, 9, 12, 9, 0, 0),
    }

    await table.insert(row=row)
    rows = [r async for r in table.select()]
    assert rows == [row]

    row["boolean"] = False
    row["date"] = date(2022, 9, 13)
    row["decimal"] = Decimal("234567.89")
    row["double"] = 23.45678901
    row["bigint"] = 1234567890
    row["string"] = "strung"
    row["timestamp"] = datetime(2021, 9, 13, 9, 0, 0)

    await table.update(row=row, where=Expression("id = ", Param(row["id"])))
    rows = [r async for r in table.select()]
    assert rows == [row]

    await table.delete(where=Expression("id = ", Param(row["id"])))
    rows = [r async for r in table.select()]
    assert len(rows) == 0

    await table.drop()


async def test_pagination(database):

    table = Table(
        database=database,
        name="foo",
        columns=[
            Column("id", "bigint", int)
        ]
    )

    await table.create(
        external=False,
        location=f"s3://fondat/lake1/{database.name}/foo/",
        properties={"table_type": "ICEBERG"},
    )

    ROW_COUNT = 10

    for n in range(ROW_COUNT):
        row = {"id": n}
        await table.insert(row=row)

    rows = [row async for row in await database.execute("SELECT id FROM foo", page_size=2)]
    assert len(rows) == ROW_COUNT

    await table.drop()