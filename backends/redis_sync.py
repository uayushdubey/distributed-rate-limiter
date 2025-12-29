from typing import Any, List, Sequence

import redis

from .base import Backend


class RedisSyncBackend(Backend):
    """
    Synchronous Redis backend using redis-py.

    This backend is safe for multi-threaded environments
    and uses Redis Lua scripts for atomicity.
    """

    def __init__(
        self,
        redis_url: str,
        *,
        socket_timeout: float = 1.0,
        socket_connect_timeout: float = 1.0,
    ):
        self._client = redis.Redis.from_url(
            redis_url,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
            decode_responses=False,  # keep raw bytes
        )

        # Local cache: script source -> Script object
        self._script_cache = {}

    def execute(
        self,
        script: str,
        keys: Sequence[str],
        args: Sequence[Any],
    ) -> List[Any]:
        # Register script lazily (redis handles SHA caching)
        lua = self._script_cache.get(script)
        if lua is None:
            lua = self._client.register_script(script)
            self._script_cache[script] = lua

        # Single round-trip execution
        return lua(keys=list(keys), args=list(args))
