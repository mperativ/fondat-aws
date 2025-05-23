"""Tests for bedrock pagination functionality."""

from fondat.aws.bedrock.pagination import paginate, decode_cursor
from fondat.pagination import Page


def test_decode_cursor_none():
    """Test decoding None cursor value."""
    assert decode_cursor(None) is None


def test_decode_cursor_bytes():
    """Test decoding bytes cursor value."""
    assert decode_cursor(b"abc") == "abc"


def test_decode_cursor_str():
    """Test decoding string cursor value."""
    assert decode_cursor("xyz") == "xyz"


def test_paginate_basic():
    """Test basic pagination functionality."""
    page = paginate({"items": [1, 2], "nextToken": "tok"}, "items")
    assert isinstance(page, Page)
    assert page.items == [1, 2]
    assert page.cursor == b"tok"
