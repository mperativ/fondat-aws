"""AWS Lambda module."""

import asyncio
import fondat.context
import fondat.http

from base64 import b64decode, b64encode
from collections.abc import Callable, Coroutine
from fondat.stream import BytesStream
from typing import Any


def async_function(
    handler: Callable[[dict[str, Any], Any], Coroutine[Any, Any, Any]],
    init: Callable[[], Coroutine[Any, Any, None]] | None = None,
    loop: asyncio.AbstractEventLoop | None = None,
):
    """
    Return an AWS Lambda function that invokes an asynchronous coroutine function with event
    and context.

    Parameters:
    • coroutine: coroutine function to invoke for each call
    • init: initialization coroutine function to invoke prior to first coroutine invocation
    • loop: event loop to run function in; None creates a new one
    """

    def function(event: dict[str, Any], context: Any) -> dict[str, Any]:
        nonlocal loop
        nonlocal init
        if not loop:
            loop = asyncio.new_event_loop()
        if init:
            loop.run_until_complete(init())
            init = None
        return loop.run_until_complete(handler(event, context))

    return function


def http_function(
    handler: Callable[[fondat.http.Request], Coroutine[Any, Any, fondat.http.Response]],
    init: Callable[[], Coroutine[Any, Any, None]] | None = None,
) -> Callable[[Any, Any], Coroutine[Any, Any, dict[str, Any]]]:
    """
    Return an AWS Lambda function to invoke an HTTP request handler.

    Parameters:
    • handler: HTTP request handler coroutine function to invoke for each call
    • init: coroutine function to invoke prior to first request handler invocation
    """

    async def http_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
        if event["version"] != "2.0":
            raise ValueError("expecting payload version: 2.0")
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
                raise ValueError("expecting HTTP protocol")
            request.method = http["method"]
            request.path = http["path"]
            request.version = version
            for key, value in event["headers"].items():
                request.headers[key] = value
            for cookie in event.get("cookies", ()):
                request.cookies.load(cookie)
            for key, value in event.get("queryStringParameters", {}).items():
                request.query[key] = value
            body = event.get("body")
            if body:
                request.body = BytesStream(
                    b64decode(body) if event["isBase64Encoded"] else body.encode(),
                    request.headers.get("content-length"),
                )
            response = await handler(request)
            headers = response.headers
            return {
                "isBase64Encoded": True,
                "statusCode": response.status,
                "headers": {k: ", ".join(headers.getall(k)) for k in headers.keys()},
                "body": (
                    b64encode(b"".join([b async for b in response.body])).decode()
                    if response.body is not None
                    else ""
                ),
            }

    return async_function(http_handler, init)
