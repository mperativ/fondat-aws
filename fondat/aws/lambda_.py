"""Fondat module for AWS Lambda."""

import asyncio
import fondat.context
import fondat.http

from base64 import b64encode, b64decode
from collections.abc import Awaitable


def http_function(handler: Awaitable):
    """Expose a Fondat HTTP request handler as an AWS Lambda function."""

    async def coroutine(event, context):
        with fondat.context.push(
            {
                "context": "fondat.aws.lambda.http",
                "lambda_event": event,
                "lambda_context": context,
            }
        ):
            request = fondat.http.Request()
            http = event["requestContext"]["http"]
            protocol, version = http["protocol"].split("/", 1)
            if protocol != "HTTP":
                raise InternalServerError("expecting HTTP protocol")
            request.method = http["method"]
            request.path = http["path"]
            request.version = version
            for key, value in event["headers"].items():
                request.header[key] = value
            for cookie in event["cookies"]:
                request.cookies.load(cookie)
            for key, value in event["queryStringParameters"].items():
                request.query[key] = value
            request.body = (
                b64decode(event["body"]) if event["isBase64Encoded"] else event["body"].encode()
            )
            response = await handler(request)
            headers = response.headers
            return {
                "isBase64Encoded": True,
                "statusCode": response.status,
                "multiValueHeaders": {k: headers.getall(k) for k in headers.keys()},
                "body": (
                    b64encode(b"".join([b async for b in response.body])).decode()
                    if response.body is not None
                    else ""
                ),
            }

    def function(event, context):
        coro = coroutine(event, context)
        try:
            asyncio.get_running_loop().run_until_complete(coro)
        except RuntimeError:
            return asyncio.run(coro)

    return function
