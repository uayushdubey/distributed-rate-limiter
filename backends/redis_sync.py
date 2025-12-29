from typing import Any, List, Sequence
import hashlib

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
        ping_on_start: bool = True,
    ):
        self._client = redis.Redis.from_url(
            redis_url,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
            decode_responses=False,  # keep raw bytes
        )

        # script_hash -> registered Lua script
        self._script_cache: dict[str, Any] = {}

        # Optional early Redis connectivity check
        if ping_on_start:
            self._client.ping()

    @staticmethod
    def _script_key(script: str) -> str:
        """
        Generate a stable hash key for Lua scripts.
        """
        return hashlib.sha256(script.encode()).hexdigest()

    def execute(
        self,
        script: str,
        keys: Sequence[str],
        args: Sequence[Any],
    ) -> List[Any]:
        key = self._script_key(script)

        lua = self._script_cache.get(key)
        if lua is None:
            lua = self._client.register_script(script)
            self._script_cache[key] = lua

        # Single round-trip execution
        return lua(keys=list(keys), args=list(args))

    def close(self) -> None:
        """
        Gracefully close the Redis connection.
        """
        self._client.close()
