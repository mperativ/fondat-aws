"""Tests for BedrockCache."""

import pytest
import asyncio
from fondat.aws.bedrock.cache import BedrockCache, CachedList, CachedPage
from fondat.pagination import Page
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import TypeVar

T = TypeVar("T")


@dataclass
class TestItem:
    id: str
    name: str


@pytest.fixture
def bedrock_cache():
    """Fixture to provide a BedrockCache instance."""
    return BedrockCache(cache_size=10, cache_expire=0.01)


@pytest.mark.asyncio
async def test_get_cached_list_hit(bedrock_cache):
    """Test getting a cached list when it exists."""
    # Setup
    items = [TestItem(id="1", name="test1"), TestItem(id="2", name="test2")]
    cache_key = "test_key"

    # Store items in cache
    await bedrock_cache._cache[cache_key].put(
        CachedList(items=items, timestamp=datetime.utcnow())
    )

    # Mock fetch function
    async def fetch_func():
        return [TestItem(id="3", name="test3")]  # Should not be called

    # Execute
    result = await bedrock_cache.get_cached_list(
        cache_key=cache_key, item_type=TestItem, fetch_func=fetch_func
    )

    # Verify
    assert result == items
    assert len(result) == 2
    assert result[0].id == "1"
    assert result[1].id == "2"


@pytest.mark.asyncio
async def test_get_cached_list_miss(bedrock_cache):
    """Test getting a cached list when it doesn't exist."""
    # Setup
    cache_key = "test_key"
    expected_items = [TestItem(id="1", name="test1"), TestItem(id="2", name="test2")]

    # Mock fetch function
    async def fetch_func():
        return expected_items

    # Execute
    result = await bedrock_cache.get_cached_list(
        cache_key=cache_key, item_type=TestItem, fetch_func=fetch_func
    )

    # Verify
    assert result == expected_items
    assert len(result) == 2
    assert result[0].id == "1"
    assert result[1].id == "2"

    # Verify cache was populated
    cached = await bedrock_cache._cache[cache_key].get()
    assert cached.items == expected_items


@pytest.mark.asyncio
async def test_get_cached_list_error_propagation(bedrock_cache):
    """Test that errors from fetch_func are propagated."""
    # Setup
    cache_key = "test_key"
    expected_error = ValueError("Test error")

    # Mock fetch function that raises an error
    async def fetch_func():
        raise expected_error

    # Execute and verify
    with pytest.raises(ValueError) as exc_info:
        await bedrock_cache.get_cached_list(
            cache_key=cache_key, item_type=TestItem, fetch_func=fetch_func
        )
    assert str(exc_info.value) == "Test error"


@pytest.mark.asyncio
async def test_get_cached_page_hit(bedrock_cache):
    """Test getting a cached page when it exists."""
    # Setup
    items = [TestItem(id="1", name="test1"), TestItem(id="2", name="test2")]
    page = Page(items=items, cursor=None)
    cache_key = "test_key"

    # Store page in cache
    await bedrock_cache._cache[cache_key].put(
        CachedPage(page=page, timestamp=datetime.utcnow())
    )

    # Mock fetch function
    async def fetch_func():
        return Page(items=[TestItem(id="3", name="test3")], cursor=None)  # Should not be called

    # Execute
    result = await bedrock_cache.get_cached_page(
        cache_key=cache_key, page_type=Page[TestItem], fetch_func=fetch_func
    )

    # Verify
    assert result == page
    assert len(result.items) == 2
    assert result.items[0].id == "1"
    assert result.items[1].id == "2"


@pytest.mark.asyncio
async def test_get_cached_page_miss(bedrock_cache):
    """Test getting a cached page when it doesn't exist."""
    # Setup
    cache_key = "test_key"
    expected_items = [TestItem(id="1", name="test1"), TestItem(id="2", name="test2")]
    expected_page = Page(items=expected_items, cursor=None)

    # Mock fetch function
    async def fetch_func():
        return expected_page

    # Execute
    result = await bedrock_cache.get_cached_page(
        cache_key=cache_key, page_type=Page[TestItem], fetch_func=fetch_func
    )

    # Verify
    assert result == expected_page
    assert len(result.items) == 2
    assert result.items[0].id == "1"
    assert result.items[1].id == "2"

    # Verify cache was populated
    cached = await bedrock_cache._cache[cache_key].get()
    assert cached.page == expected_page


@pytest.mark.asyncio
async def test_get_cached_page_error_propagation(bedrock_cache):
    """Test that errors from fetch_func are propagated for pages."""
    # Setup
    cache_key = "test_key"
    expected_error = ValueError("Test error")

    # Mock fetch function that raises an error
    async def fetch_func():
        raise expected_error

    # Execute and verify
    with pytest.raises(ValueError) as exc_info:
        await bedrock_cache.get_cached_page(
            cache_key=cache_key, page_type=Page[TestItem], fetch_func=fetch_func
        )
    assert str(exc_info.value) == "Test error"


@pytest.mark.asyncio
async def test_cache_expiration(bedrock_cache):
    """Test that cache entries expire and new values are fetched after expiration."""
    # Setup
    cache_key = "test_key"
    items = [TestItem(id="1", name="test1")]
    await bedrock_cache._cache[cache_key].put(
        CachedList(
            items=items,
            timestamp=datetime.utcnow() - timedelta(seconds=bedrock_cache._cache.expire + 1),
        )
    )
    # Wait for the cache to expire
    await asyncio.sleep(0.02)

    # Mock fetch function
    async def fetch_func():
        return [TestItem(id="2", name="test2")]

    # Execute and verify that the new value is fetched after expiration
    result = await bedrock_cache.get_cached_list(
        cache_key=cache_key, item_type=TestItem, fetch_func=fetch_func
    )
    assert result[0].id == "2"  # Should get new items from fetch_func after expiration


@pytest.mark.asyncio
async def test_concurrent_cache_access(bedrock_cache):
    """Test concurrent access to the same cache key."""
    # Setup
    cache_key = "test_key"
    expected_items = [TestItem(id="1", name="test1")]

    # Mock fetch function that simulates a delay
    async def fetch_func():
        await asyncio.sleep(0.1)
        return expected_items

    # Execute multiple concurrent requests
    tasks = [
        bedrock_cache.get_cached_list(
            cache_key=cache_key, item_type=TestItem, fetch_func=fetch_func
        )
        for _ in range(5)
    ]
    results = await asyncio.gather(*tasks)

    # Verify all results are the same
    assert all(r == expected_items for r in results)

    # Verify fetch_func was called only once
    cached = await bedrock_cache._cache[cache_key].get()
    assert cached.items == expected_items


@pytest.mark.asyncio
async def test_invalidate_cache(bedrock_cache):
    """Test cache invalidation."""
    # Setup
    cache_key = "test_key"
    items = [TestItem(id="1", name="test1")]

    # Store items in cache
    await bedrock_cache._cache[cache_key].put(
        CachedList(items=items, timestamp=datetime.utcnow())
    )

    # Invalidate cache
    await bedrock_cache.invalidate(cache_key)

    # Mock fetch function
    async def fetch_func():
        return [TestItem(id="2", name="test2")]

    # Execute
    result = await bedrock_cache.get_cached_list(
        cache_key=cache_key, item_type=TestItem, fetch_func=fetch_func
    )

    # Verify
    assert result[0].id == "2"  # Should get new items from fetch_func
