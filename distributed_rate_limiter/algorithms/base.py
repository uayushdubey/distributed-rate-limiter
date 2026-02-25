from abc import ABC, abstractmethod
from typing import Any, Sequence


class RateLimitAlgorithm(ABC):
    """
    Base interface for all rate limiting algorithms.

    Implementations MUST:
    - Be deterministic
    - Use Redis Lua scripts for atomicity
    - Never rely on Python time
    """

    #: Human-readable algorithm name (used in Redis key namespace)
    name: str

    # -----------------------------------------------------
    # Required Methods
    # -----------------------------------------------------

    @abstractmethod
    def lua_script(self) -> str:
        """
        Return the Lua script implementing the algorithm.
        """
        raise NotImplementedError

    @abstractmethod
    def static_args(self) -> Sequence[Any]:
        """
        Return static algorithm arguments (rate, period, burst, etc).

        These are constant per limiter instance.
        """
        raise NotImplementedError

    # -----------------------------------------------------
    # Optional Overrides
    # -----------------------------------------------------

    def dynamic_args(self, **kwargs) -> Sequence[Any]:
        """
        Return request-level arguments (e.g., cost, weight).

        Default: no dynamic arguments.
        """
        return []

    def redis_key_suffix(self) -> str:
        """
        Short identifier used in Redis key namespacing.
        """
        return self.name