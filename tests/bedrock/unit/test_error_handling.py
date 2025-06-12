"""Tests for error handling in Bedrock resources."""

import pytest
import botocore.exceptions
import fondat.error
from fondat.aws.client import wrap_client_error


@pytest.mark.asyncio
async def test_wrap_client_error_basic():
    """Test basic error wrapping functionality."""
    # Test BadRequestError
    with pytest.raises(fondat.error.BadRequestError):
        with wrap_client_error():
            raise botocore.exceptions.ClientError(
                error_response={
                    "Error": {"Code": "ValidationException"},
                    "ResponseMetadata": {"HTTPStatusCode": 400},
                },
                operation_name="TestOperation",
            )

    # Test NotFoundError
    with pytest.raises(fondat.error.NotFoundError):
        with wrap_client_error():
            raise botocore.exceptions.ClientError(
                error_response={
                    "Error": {"Code": "ResourceNotFoundException"},
                    "ResponseMetadata": {"HTTPStatusCode": 404},
                },
                operation_name="TestOperation",
            )

    # Test ForbiddenError
    with pytest.raises(fondat.error.ForbiddenError):
        with wrap_client_error():
            raise botocore.exceptions.ClientError(
                error_response={
                    "Error": {"Code": "AccessDeniedException"},
                    "ResponseMetadata": {"HTTPStatusCode": 403},
                },
                operation_name="TestOperation",
            )

    # Test ConflictError
    with pytest.raises(fondat.error.ConflictError):
        with wrap_client_error():
            raise botocore.exceptions.ClientError(
                error_response={
                    "Error": {"Code": "ConflictException"},
                    "ResponseMetadata": {"HTTPStatusCode": 409},
                },
                operation_name="TestOperation",
            )

    # Test TooManyRequestsError: expect the error from fondat.error.errors[429] for throttling
    with pytest.raises(fondat.error.errors[429]):
        with wrap_client_error():
            raise botocore.exceptions.ClientError(
                error_response={
                    "Error": {"Code": "ThrottlingException"},
                    "ResponseMetadata": {"HTTPStatusCode": 429},
                },
                operation_name="TestOperation",
            )

    # Test InternalServerError for unknown error codes
    with pytest.raises(fondat.error.InternalServerError):
        with wrap_client_error():
            raise botocore.exceptions.ClientError(
                error_response={
                    "Error": {"Code": "UnknownError"},
                    "ResponseMetadata": {"HTTPStatusCode": 500},
                },
                operation_name="TestOperation",
            )


@pytest.mark.asyncio
async def test_wrap_client_error_preserves_original():
    """Test that wrap_client_error preserves the original error as the cause."""
    original_error = botocore.exceptions.ClientError(
        error_response={
            "Error": {"Code": "ValidationException"},
            "ResponseMetadata": {"HTTPStatusCode": 400},
        },
        operation_name="TestOperation",
    )
    
    with pytest.raises(fondat.error.BadRequestError) as exc_info:
        with wrap_client_error():
            raise original_error
    
    assert exc_info.value.__cause__ is original_error


@pytest.mark.asyncio
async def test_wrap_client_error_non_client_error():
    """Test that non-ClientError exceptions are not wrapped."""
    with pytest.raises(ValueError):
        with wrap_client_error():
            raise ValueError("Test error")


@pytest.mark.asyncio
async def test_wrap_client_error_missing_metadata():
    """Test handling of ClientError with missing metadata."""
    # If ResponseMetadata is missing, should raise KeyError
    with pytest.raises(KeyError):
        with wrap_client_error():
            raise botocore.exceptions.ClientError(
                error_response={
                    "Error": {"Code": "ValidationException"},
                },
                operation_name="TestOperation",
            )


@pytest.mark.asyncio
async def test_wrap_client_error_missing_error_code():
    """Test handling of ClientError with missing error code."""
    # If Error is missing, should raise KeyError
    with pytest.raises(KeyError):
        with wrap_client_error():
            raise botocore.exceptions.ClientError(
                error_response={
                    "ResponseMetadata": {"HTTPStatusCode": 400},
                },
                operation_name="TestOperation",
            )


@pytest.mark.asyncio
async def test_wrap_client_error_invalid_status_code():
    """Test handling of ClientError with invalid status code."""
    with pytest.raises(KeyError):
        with wrap_client_error():
            raise botocore.exceptions.ClientError(
                error_response={
                    "Error": {"Code": "ValidationException"},
                    "ResponseMetadata": {"HTTPStatusCode": 999},
                },
                operation_name="TestOperation",
            )


@pytest.mark.asyncio
async def test_wrap_client_error_nested():
    """Test nested usage of wrap_client_error."""
    with pytest.raises(fondat.error.BadRequestError):
        with wrap_client_error():
            with wrap_client_error():
                raise botocore.exceptions.ClientError(
                    error_response={
                        "Error": {"Code": "ValidationException"},
                        "ResponseMetadata": {"HTTPStatusCode": 400},
                    },
                    operation_name="TestOperation",
                )


@pytest.mark.asyncio
async def test_wrap_client_error_with_context():
    """Test wrap_client_error with additional message."""
    error_message = "Invalid parameter value"
    with pytest.raises(fondat.error.BadRequestError):
        with wrap_client_error():
            raise botocore.exceptions.ClientError(
                error_response={
                    "Error": {
                        "Code": "ValidationException",
                        "Message": error_message,
                    },
                    "ResponseMetadata": {"HTTPStatusCode": 400},
                },
                operation_name="TestOperation",
            )
