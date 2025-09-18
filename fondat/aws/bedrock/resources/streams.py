from collections.abc import AsyncIterator
from types import TracebackType
from typing import Any, Optional, Type

class FlowStream(AsyncIterator[dict]):
    """
    Async iterator that keeps the underlying runtime_client session alive
    until the caller finishes iterating, then closes it cleanly.
    """

    def __init__(self, response: dict, client_cm):
        # response is the original dict returned by invoke_flow
        self._response = response
        self._client_cm = client_cm
        self._closed = False
        stream = response.get("responseStream")
        if hasattr(stream, "__aiter__"):
            # Async iterator (aiobotocore)
            self._stream_async = True
            self._async_iter = stream.__aiter__()
        else:
            # Sync iterator (botocore EventStream)
            self._stream_async = False
            self._sync_iter = iter(stream)

    # ------------- async iterator protocol -------------
    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            if self._stream_async:
                # Async iteration
                return await self._async_iter.__anext__()
            else:
                # Sync iteration
                return next(self._sync_iter)
        except (StopAsyncIteration, StopIteration):
            # auto-close when stream ends
            await self.close()
            raise StopAsyncIteration

    # ------------- async context-manager helpers -------------
    async def __aenter__(self):
        # let users do:  async with stream as s:
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ):
        await self.close()

    # ------------- public helper -------------
    async def close(self):
        """Close the underlying aiohttp session if not already closed."""
        if not self._closed:
            await self._client_cm.__aexit__(None, None, None)
            self._closed = True


class AgentStream(AsyncIterator[dict]):
    """
    Async iterator that keeps the underlying runtime_client session alive
    until the caller finishes iterating, then closes it cleanly.
    Handles agent completion streams from invoke_agent.
    """

    def __init__(self, response: dict, client_cm):
        # response is the original dict returned by invoke_agent
        self._response = response
        self._client_cm = client_cm
        self._closed = False
        stream = response.get("completion")
        if hasattr(stream, "__aiter__"):
            # Async iterator (aiobotocore)
            self._stream_async = True
            self._async_iter = stream.__aiter__()
        else:
            # Sync iterator (botocore EventStream)
            self._stream_async = False
            self._sync_iter = iter(stream)

    # ------------- async iterator protocol -------------
    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            if self._stream_async:
                # Async iteration
                return await self._async_iter.__anext__()
            else:
                # Sync iteration
                return next(self._sync_iter)
        except (StopAsyncIteration, StopIteration):
            # auto-close when stream ends
            await self.close()
            raise StopAsyncIteration

    # ------------- async context-manager helpers -------------
    async def __aenter__(self):
        # let users do:  async with stream as s:
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ):
        await self.close()

    # ------------- public helper -------------
    async def close(self):
        """Close the underlying aiohttp session if not already closed."""
        if not self._closed:
            await self._client_cm.__aexit__(None, None, None)
            self._closed = True