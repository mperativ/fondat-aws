"""Caching implementation for Bedrock list operations."""

from fondat.memory import MemoryResource
from typing import TypeVar, Generic, Type
from dataclasses import dataclass
from datetime import datetime
from fondat.pagination import Page

T = TypeVar("T")


@dataclass
class CachedList(Generic[T]):
    """Wrapper for cached list results with timestamp."""

    items: list[T]
    timestamp: datetime


@dataclass
class CachedPage(Generic[T]):
    """Wrapper for cached page results with timestamp."""

    page: Page[T]
    timestamp: datetime


class BedrockCache:
    """Cache manager for Bedrock list operations."""

    def __init__(
        self,
        cache_size: int = 100,
        cache_expire: int | float = 300,  # 5 minutes default
    ):
        """Initialize Bedrock cache.

        Args:
            cache_size: Maximum number of items to cache
            cache_expire: Cache expiration time in seconds
        """
        self._cache = MemoryResource(
            key_type=str,
            value_type=CachedList,
            size=cache_size,
            evict=True,
            expire=cache_expire,
        )

    async def get_cached_list(
        self, cache_key: str, item_type: Type[T], fetch_func: callable, *args, **kwargs
    ) -> list[T]:
        """Get a cached list or fetch it if not cached.

        Args:
            cache_key: Unique key for the cache entry
            item_type: Type of items in the list
            fetch_func: Async function to fetch the list if not cached
            *args: Arguments to pass to fetch_func
            **kwargs: Keyword arguments to pass to fetch_func

        Returns:
            List of items of type T
        """
        try:
            cached = await self._cache[cache_key].get()
            return cached.items
        except Exception:
            items = await fetch_func(*args, **kwargs)
            await self._cache[cache_key].put(
                CachedList(items=items, timestamp=datetime.utcnow())
            )
            return items

    async def get_cached_page(
        self, cache_key: str, page_type: Type[Page[T]], fetch_func: callable, *args, **kwargs
    ) -> Page[T]:
        """Get a cached page or fetch it if not cached.

        Args:
            cache_key: Unique key for the cache entry
            page_type: Type of the page and its items
            fetch_func: Async function to fetch the page if not cached
            *args: Arguments to pass to fetch_func
            **kwargs: Keyword arguments to pass to fetch_func

        Returns:
            Page of items of type T
        """
        try:
            cached = await self._cache[cache_key].get()
            return cached.page
        except Exception:
            page = await fetch_func(*args, **kwargs)
            await self._cache[cache_key].put(CachedPage(page=page, timestamp=datetime.utcnow()))
            return page

    async def invalidate(self, cache_key: str):
        """Invalidate a specific cache entry."""
        try:
            await self._cache[cache_key].delete()
        except Exception:
            pass
