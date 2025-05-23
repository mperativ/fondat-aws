"""Pagination helpers for Bedrock operations."""

from typing import Any, Mapping
from fondat.pagination import Page, Cursor


def paginate(resp: Mapping[str, Any], items_key: str) -> Page[Mapping[str, Any]]:
    """
    Wrap a botocore response into a Fondat Page, extracting items and cursor.

    Args:
        resp: The response from botocore containing items and optional nextToken
        items_key: The key in the response containing the items list

    Returns:
        A Page containing the items and cursor
    """
    items = resp.get(items_key, [])
    token = resp.get("nextToken")
    cursor = token.encode() if token else None
    return Page(items=items, cursor=cursor)


def decode_cursor(cursor: Cursor | None) -> str | None:
    """
    Decode a Fondat cursor into a botocore nextToken.

    Args:
        cursor: The Fondat cursor to decode

    Returns:
        The decoded nextToken string or None
    """
    if cursor is None:
        return None
    return cursor.decode() if isinstance(cursor, bytes) else cursor
