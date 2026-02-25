from typing import Any, List, Sequence
import hashlib

from redis.exceptions import RedisError
from .base import AsyncBackend


class RedisAsyncBackend(AsyncBackend):
    """
    Enterprise-grade asynchronous Redis backend.

    Features:
    - Lua script caching
    - Lazy connection validation
    - Health checks
    - Script cache reset on Redis restart
    - Single round-trip execution
    """

    def __init__(
        self,
        redis_url: str,
        *,
        socket_timeout: float = 1.0,
        socket_connect_timeout: float = 1.0,
        max_connections: int = 100,
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
            max_connections=max_connections,
            decode_responses=False,
        )

        self._script_cache: dict[str, Any] = {}
        self._ping_on_start = ping_on_start

    # -----------------------------------------------------
    # Connection Handling
    # -----------------------------------------------------

    async def _ensure_connection(self) -> None:
        if self._ping_on_start:
            await self._client.ping()
            self._ping_on_start = False

    async def health_check(self) -> bool:
        try:
            await self._client.ping()
            return True
        except RedisError:
            return False

    async def get_time(self) -> float:
        """
        Get Redis server time (seconds).
        Useful for debugging / observability.
        """
        seconds, microseconds = await self._client.time()
        return seconds + (microseconds / 1_000_000)

    # -----------------------------------------------------
    # Script Utilities
    # -----------------------------------------------------

    @staticmethod
    def _script_key(script: str) -> str:
        return hashlib.sha256(script.encode()).hexdigest()

    async def _get_or_register_script(self, script: str):
        key = self._script_key(script)

        lua = self._script_cache.get(key)
        if lua is None:
            lua = self._client.register_script(script)
            self._script_cache[key] = lua

        return lua

    # -----------------------------------------------------
    # Core Execution
    # -----------------------------------------------------

    async def execute(
        self,
        script: str,
        keys: Sequence[str],
        args: Sequence[Any],
    ) -> List[Any]:
        await self._ensure_connection()

        try:
            lua = await self._get_or_register_script(script)
            return await lua(keys=list(keys), args=list(args))

        except RedisError as exc:
            # Clear script cache in case Redis restarted
            self._script_cache.clear()
            raise exc

    # -----------------------------------------------------
    # Cleanup
    # -----------------------------------------------------

    async def close(self) -> None:
        await self._client.close()