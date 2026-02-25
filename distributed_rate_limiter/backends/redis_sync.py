from typing import Any, List, Sequence, Optional
import hashlib
import redis
from redis.exceptions import RedisError

from .base import Backend


class RedisSyncBackend(Backend):
    """
    Enterprise-grade synchronous Redis backend.

    Features:
    - Lua script caching
    - NOSCRIPT safe execution
    - Health checks
    - Configurable connection pool
    - Timeout hardened
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
        self._client = redis.Redis.from_url(
            redis_url,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
            max_connections=max_connections,
            decode_responses=False,
        )

        self._script_cache: dict[str, Any] = {}

        if ping_on_start:
            self._client.ping()

    # --------------------------
    # Script Utilities
    # --------------------------

    @staticmethod
    def _script_key(script: str) -> str:
        return hashlib.sha256(script.encode()).hexdigest()

    def _get_or_register_script(self, script: str):
        key = self._script_key(script)

        lua = self._script_cache.get(key)
        if lua is None:
            lua = self._client.register_script(script)
            self._script_cache[key] = lua

        return lua

    # --------------------------
    # Core Execution
    # --------------------------

    def execute(
        self,
        script: str,
        keys: Sequence[str],
        args: Sequence[Any],
    ) -> List[Any]:
        """
        Execute Lua script atomically.

        Handles:
        - Script caching
        - NOSCRIPT fallback
        - Redis errors
        """
        lua = self._get_or_register_script(script)

        try:
            return lua(keys=list(keys), args=list(args))

        except RedisError as exc:
            # Safety: clear cache if Redis restarted
            self._script_cache.clear()
            raise exc

    # --------------------------
    # Health & Utility
    # --------------------------

    def health_check(self) -> bool:
        """
        Returns True if Redis is reachable.
        """
        try:
            return self._client.ping()
        except RedisError:
            return False

    def get_time(self) -> float:
        """
        Get Redis server time (seconds).
        Useful for debugging / observability.
        """
        seconds, microseconds = self._client.time()
        return seconds + (microseconds / 1_000_000)

    def close(self) -> None:
        self._client.close()