from collections.abc import AsyncIterator
from types import TracebackType
from typing import Any, Optional, Type

class BaseStream(AsyncIterator[dict]):
    """
    Shared async iterator/context manager for Bedrock event streams.
    Subclasses provide the stream key present in the response dict.
    """

    def __init__(self, response: dict, client_cm, stream_key: str):
        self._response = response
        self._client_cm = client_cm
        self._closed = False
        stream = response.get(stream_key)
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


class FlowStream(BaseStream):
    """
    Async iterator for flow streams from invoke_flow.
    """

    def __init__(self, response: dict, client_cm):
        super().__init__(response, client_cm, "responseStream")


class AgentStream(BaseStream):
    """
    Async iterator for agent completion streams from invoke_agent.
    """

    def __init__(self, response: dict, client_cm):
        super().__init__(response, client_cm, "completion")