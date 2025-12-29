from typing import Callable, Optional, Tuple

from .types import RateLimitInfo
from .exceptions import ConfigurationError


class RateLimiter:
    """
    Public entry point for distributed rate limiting.
    Framework-agnostic and horizontally scalable.
    """

    def __init__(
        self,
        *,
        rate: int,
        per: int,
        redis_url: str,
        algorithm: str = "token_bucket",
        namespace: str = "default",
        fail_strategy: str = "open",
        async_mode: bool = False,
        key_func: Optional[Callable] = None,
        on_allow: Optional[Callable] = None,
        on_block: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
    ):
        if rate <= 0:
            raise ConfigurationError("rate must be > 0")

        if per <= 0:
            raise ConfigurationError("per must be > 0")

        if fail_strategy not in {"open", "closed"}:
            raise ConfigurationError(
                "fail_strategy must be either 'open' or 'closed'"
            )

        self.rate = rate
        self.per = per
        self.redis_url = redis_url
        self.algorithm = algorithm
        self.namespace = namespace
        self.fail_strategy = fail_strategy
        self.async_mode = async_mode

        self.key_func = key_func
        self.on_allow = on_allow
        self.on_block = on_block
        self.on_error = on_error

    def _validate_identity(self, identity: str) -> None:
        if not isinstance(identity, str):
            raise ConfigurationError("identity must be a string")

        if not identity:
            raise ConfigurationError("identity cannot be empty")

        if len(identity) > 1024:
            raise ConfigurationError("identity is too long")

    def allow(self, identity: str) -> Tuple[bool, Optional[RateLimitInfo]]:
        if self.async_mode:
            raise RuntimeError(
                "allow() cannot be used when async_mode=True"
            )

        self._validate_identity(identity)
        raise NotImplementedError

    async def allow_async(self, identity: str) -> Tuple[bool, Optional[RateLimitInfo]]:
        if not self.async_mode:
            raise RuntimeError(
                "allow_async() requires async_mode=True"
            )

        self._validate_identity(identity)
        raise NotImplementedError
