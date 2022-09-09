import asyncio
import fondat.aws.athena as athena

from datetime import date, datetime
from decimal import Decimal
from fondat.aws.athena import Expression, Param
from fondat.types import literal_values
from types import NoneType
from typing import Literal, TypedDict
from uuid import UUID, uuid4


db = athena.Database(name="db1", workgroup="primary")


async def _test_values(type, *values):
    stmt = Expression("SELECT ")
    v = []
    for n in range(len(values)):
        v.append(Expression(Param(values[n], type), f" AS v{n}"))
    stmt += Expression.join(v, ", ")
    stmt += ";"
    TD = TypedDict("TD", {f"v{n}": type for n in range(len(values))})
    async for row in await db.execute(stmt, result_type=TD):
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


async def test_uuid():
    await _test_values(UUID, UUID("2093f88a-99ab-4807-87f7-ab3997a199b5"), uuid4())


async def test_none():
    await _test_values(NoneType, None)


async def test_union():
    UT = str | None
    await _test_values(UT, "a", None)


async def test_literal():
    L = Literal["a", "b", "c"]
    await _test_values(L, *literal_values(L))
