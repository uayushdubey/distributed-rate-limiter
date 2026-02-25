import hashlib
from typing import Callable, Optional, Tuple

from .types import RateLimitInfo
from .exceptions import (
    ConfigurationError,
    BackendUnavailable,
    IdentityError,
    BackendExecutionError,
    AlgorithmError,
)
from .algorithms import TokenBucket
from .backends import RedisSyncBackend, RedisAsyncBackend


class RateLimiter:
    """
    Enterprise-grade distributed rate limiter.
    """

    def __init__(
        self,
        *,
        rate: int,
        per: int,
        redis_url: str,
        burst: Optional[int] = None,
        algorithm: str = "token_bucket",
        namespace: str = "default",
        fail_strategy: str = "open",
        async_mode: bool = False,
        key_func: Optional[Callable[[str], str]] = None,
        on_allow: Optional[Callable] = None,
        on_block: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
    ):
        # ---------------- Validation ----------------
        if rate <= 0 or per <= 0:
            raise ConfigurationError("rate and per must be > 0")

        if fail_strategy not in {"open", "closed"}:
            raise ConfigurationError(
                "fail_strategy must be 'open' or 'closed'"
            )

        if algorithm != "token_bucket":
            raise ConfigurationError(
                f"Unsupported algorithm: {algorithm}"
            )

        # ---------------- Config ----------------
        self.rate = rate
        self.per = per
        self.burst = burst if burst is not None else rate
        self.namespace = namespace
        self.fail_strategy = fail_strategy
        self.async_mode = async_mode

        self.key_func = key_func
        self.on_allow = on_allow
        self.on_block = on_block
        self.on_error = on_error

        # ---------------- Algorithm ----------------
        self.algorithm = TokenBucket(rate, per, self.burst)
        self._lua_script = self.algorithm.lua_script()

        # ---------------- Backend ----------------
        if async_mode:
            self.backend = RedisAsyncBackend(redis_url)
        else:
            self.backend = RedisSyncBackend(redis_url)

    # =====================================================
    # Internal helpers
    # =====================================================

    @staticmethod
    def _hash_identity(identity: str) -> str:
        return hashlib.sha256(identity.encode()).hexdigest()

    def _build_key(self, identity: str) -> str:
        raw = self.key_func(identity) if self.key_func else identity
        hashed = self._hash_identity(raw)
        return f"{self.namespace}:{self.algorithm.redis_key_suffix()}:{hashed}"

    @staticmethod
    def _validate_identity(identity: str) -> None:
        if not isinstance(identity, str):
            raise IdentityError("identity must be a string")

        if not identity:
            raise IdentityError("identity cannot be empty")

        if len(identity) > 1024:
            raise IdentityError("identity is too long")

    def _build_args(self, cost: int):
        return [
            *self.algorithm.static_args(),
            *self.algorithm.dynamic_args(cost=cost),
        ]

    def _handle_backend_failure(self, exc: Exception):
        if self.on_error:
            self.on_error(exc)

        if self.fail_strategy == "closed":
            raise BackendUnavailable from exc

        # fail-open
        return True, None

    # =====================================================
    # Sync API
    # =====================================================

    def allow(
        self, identity: str, *, cost: int = 1
    ) -> Tuple[bool, Optional[RateLimitInfo]]:

        if self.async_mode:
            raise RuntimeError(
                "allow() cannot be used when async_mode=True"
            )

        self._validate_identity(identity)

        if cost <= 0:
            raise ConfigurationError("cost must be > 0")

        redis_key = self._build_key(identity)

        try:
            result = self.backend.execute(
                script=self._lua_script,
                keys=[redis_key],
                args=self._build_args(cost),
            )

            if not isinstance(result, (list, tuple)) or len(result) != 3:
                raise AlgorithmError(
                    "Algorithm returned invalid response"
                )

            allowed, remaining, reset = result

            info = RateLimitInfo(
                limit=self.rate,
                remaining=int(remaining),
                reset=int(reset),
                allowed=bool(allowed),
                cost=cost,
            )

            if info.allowed:
                if self.on_allow:
                    self.on_allow(identity, info)
            else:
                if self.on_block:
                    self.on_block(identity, info)

            return info.allowed, info

        except Exception as exc:
            return self._handle_backend_failure(exc)

    # =====================================================
    # Async API
    # =====================================================

    async def allow_async(
        self, identity: str, *, cost: int = 1
    ) -> Tuple[bool, Optional[RateLimitInfo]]:

        if not self.async_mode:
            raise RuntimeError(
                "allow_async() requires async_mode=True"
            )

        self._validate_identity(identity)

        if cost <= 0:
            raise ConfigurationError("cost must be > 0")

        redis_key = self._build_key(identity)

        try:
            result = await self.backend.execute(
                script=self._lua_script,
                keys=[redis_key],
                args=self._build_args(cost),
            )

            if not isinstance(result, (list, tuple)) or len(result) != 3:
                raise AlgorithmError(
                    "Algorithm returned invalid response"
                )

            allowed, remaining, reset = result

            info = RateLimitInfo(
                limit=self.rate,
                remaining=int(remaining),
                reset=int(reset),
                allowed=bool(allowed),
                cost=cost,
            )

            if info.allowed:
                if self.on_allow:
                    self.on_allow(identity, info)
            else:
                if self.on_block:
                    self.on_block(identity, info)

            return info.allowed, info

        except Exception as exc:
            return self._handle_backend_failure(exc)