import pytest

import fondat.error

from fondat.aws import Client, Config
from fondat.aws.ses import ses_resource


pytestmark = pytest.mark.asyncio


config = Config(
    endpoint_url="http://localhost:4566",
    aws_access_key_id="id",
    aws_secret_access_key="secret",
    region_name="us-east-1",
)


@pytest.fixture(scope="function")
async def client():
    async with Client(service_name="ses", config=config) as client:
        yield client


@pytest.fixture(scope="function")
async def resource(client):
    yield ses_resource(client)


@pytest.fixture(scope="module")
async def init_verified():
    await resource.identities.post("source@test.io")


async def test_send_raw_verified_identity(resource):
    await resource.send_raw_email("source@test.io", "destination@test.io", b"message")


async def test_send_unverified_identity(resource):
    with pytest.raises(fondat.error.BadRequestError):
        await resource.send_raw_email("unverified@test.io", "destination@test.io", b"message")


async def test_verify_delete(resource):
    await resource.identities.post("verify_delete@test.io")
    await resource.identities["verify_delete@test.io"].delete()
