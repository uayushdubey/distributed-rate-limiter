from typing import Any, List, Sequence
import hashlib

from .base import AsyncBackend


class RedisAsyncBackend(AsyncBackend):
    """
    Asynchronous Redis backend using redis.asyncio.

    Requires: redis>=4.2 with asyncio support.
    """

    def __init__(
        self,
        redis_url: str,
        *,
        socket_timeout: float = 1.0,
        socket_connect_timeout: float = 1.0,
        ping_on_start: bool = True,
    ):
        try:
            from redis.asyncio import Redis
        except ImportError as exc:
            raise RuntimeError(
                "Async Redis backend requires redis>=4.2 "
                "installed with asyncio support"
            ) from exc

        self._client = Redis.from_url(
            redis_url,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
            decode_responses=False,
        )

        # script_hash -> registered Lua script
        self._script_cache: dict[str, Any] = {}

        # Optional early validation of Redis connectivity
        self._ping_on_start = ping_on_start

    async def _ensure_connection(self) -> None:
        """
        Validate Redis connectivity if ping_on_start is enabled.
        Executed lazily to avoid blocking __init__.
        """
        if self._ping_on_start:
            await self._client.ping()
            self._ping_on_start = False  # run only once

    @staticmethod
    def _script_key(script: str) -> str:
        """
        Generate a stable hash key for Lua scripts.
        """
        return hashlib.sha256(script.encode()).hexdigest()

    async def execute(
        self,
        script: str,
        keys: Sequence[str],
        args: Sequence[Any],
    ) -> List[Any]:
        await self._ensure_connection()

        key = self._script_key(script)

        lua = self._script_cache.get(key)
        if lua is None:
            lua = self._client.register_script(script)
            self._script_cache[key] = lua

        return await lua(keys=list(keys), args=list(args))

    async def close(self) -> None:
        """
        Gracefully close the Redis connection.
        """
        await self._client.close()
