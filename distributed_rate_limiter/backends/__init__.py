"""
Backend implementations for distributed-rate-limiter.

This module exposes:
- Abstract backend contracts (sync & async)
- Redis-backed implementations (sync & async)

Backends are responsible ONLY for executing Lua scripts atomically.
They must not contain rate-limiting logic.
"""

from .base import Backend, AsyncBackend
from .redis_sync import RedisSyncBackend
from .redis_async import RedisAsyncBackend

__all__ = (
    "Backend",
    "AsyncBackend",
    "RedisSyncBackend",
    "RedisAsyncBackend",
)
