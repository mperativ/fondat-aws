from dataclasses import dataclass
from fondat.aws.bedrock.pagination import paginate, decode_cursor
from fondat.pagination import Page


@dataclass
class TestItem:
    id: str
    name: str


def test_pagination():
    # Test with items and nextToken
    response = {
        "items": [{"id": "1", "name": "test1"}, {"id": "2", "name": "test2"}],
        "nextToken": "next_page",
    }
    result = paginate(response, "items")
    assert isinstance(result, Page)
    assert result.items == response["items"]
    assert result.cursor == b"next_page"


def test_pagination_with_mapper():
    # Test with items, nextToken and mapper
    response = {
        "items": [{"id": "1", "name": "test1"}, {"id": "2", "name": "test2"}],
        "nextToken": "next_page",
    }
    result = paginate(response, "items", lambda x: TestItem(**x))
    assert isinstance(result, Page)
    assert len(result.items) == 2
    assert all(isinstance(item, TestItem) for item in result.items)
    assert result.items[0].id == "1"
    assert result.items[0].name == "test1"
    assert result.cursor == b"next_page"


def test_pagination_empty():
    # Test with empty items list
    response = {"items": []}
    result = paginate(response, "items")
    assert isinstance(result, Page)
    assert result.items == []
    assert result.cursor is None


def test_pagination_no_items_key():
    # Test with missing items key
    response = {"nextToken": "next_page"}
    result = paginate(response, "items")
    assert isinstance(result, Page)
    assert result.items == []
    assert result.cursor == b"next_page"


def test_pagination_no_next_token():
    # Test without nextToken
    response = {"items": [{"id": "1", "name": "test1"}]}
    result = paginate(response, "items")
    assert isinstance(result, Page)
    assert result.items == response["items"]
    assert result.cursor is None


def test_decode_cursor():
    # Test with bytes cursor
    cursor = b"next_page"
    assert decode_cursor(cursor) == "next_page"

    # Test with string cursor
    cursor = "next_page"
    assert decode_cursor(cursor) == "next_page"

    # Test with None cursor
    assert decode_cursor(None) is None
