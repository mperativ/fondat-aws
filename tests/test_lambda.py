import fondat.http
import http
import multidict

from base64 import b64encode, b64decode
from fondat.aws.lambda_ import http_function
from fondat.resource import resource, operation


def _cimultidict(multiValueHeaders):
    result = multidict.CIMultiDict()
    for k, vs in multiValueHeaders.items():
        for v in vs:
            result.add(k, v)
    return result


def _event(
    *,
    path: str,
    method: str,
    body: bytes = b"",
):
    return {
        "version": "2.0",
        "routeKey": "$default",
        "rawPath": path,
        "rawQueryString": "",
        "cookies": [],
        "headers": {},
        "queryStringParameters": {},
        "requestContext": {
            "authorizer": {},
            "domainName": "localhost",
            "domainPrefix": "",
            "http": {
                "method": method,
                "path": path,
                "protocol": "HTTP/1.1",
                "sourceIp": "127.0.0.1",
                "userAgent": "test",
            },
            "request_id": "id",
            "routeKey": "$default",
            "stage": "$default",
            "time": "12/Mar/2020:19:03:58 +0000",
            "timeEpoch": 1583348638390,
        },
        "body": b64encode(body).decode(),
        "pathParameters": {},
        "isBase64Encoded": True,
        "stageVariables": {},
    }


def test_simple():
    @resource
    class Resource:
        @operation
        async def get(self) -> str:
            return "str"

    function = http_function(fondat.http.Application(Resource()))
    response = function(_event(path="/", method="GET"), {})
    headers = _cimultidict(response["multiValueHeaders"])

    assert response["statusCode"] == http.HTTPStatus.OK.value
    assert headers["content-type"] == "text/plain; charset=UTF-8"
    assert headers["content-length"] == "3"
    assert b64decode(response["body"]) == b"str"
