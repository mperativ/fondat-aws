import asyncio

from fondat.aws import Service, Config


config = Config(
    endpoint_url="http://localhost:4566",
    aws_access_key_id="id",
    aws_secret_access_key="secret",
    region_name="us-east-1",
)


def test_switch_event_loop():
    service = Service(name="secretsmanager", config=config)
    loop1 = asyncio.get_event_loop()
    client = loop1.run_until_complete(service.client())
    loop1.run_until_complete(client.list_secrets())
    loop2 = asyncio.new_event_loop()
    asyncio.set_event_loop(loop2)
    client = loop2.run_until_complete(service.client())
    loop2.run_until_complete(client.list_secrets())
    asyncio.set_event_loop(loop1)
    client = loop1.run_until_complete(service.client())
    loop1.run_until_complete(client.list_secrets())
