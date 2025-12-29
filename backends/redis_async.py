from typing import Any, List, Sequence

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

        self._script_cache = {}

    async def execute(
        self,
        script: str,
        keys: Sequence[str],
        args: Sequence[Any],
    ) -> List[Any]:
        lua = self._script_cache.get(script)
        if lua is None:
            lua = self._client.register_script(script)
            self._script_cache[script] = lua

        return await lua(keys=list(keys), args=list(args))
