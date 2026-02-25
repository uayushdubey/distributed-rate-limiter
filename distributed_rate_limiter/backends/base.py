from abc import ABC, abstractmethod
from typing import Any, List, Sequence


# ==========================================================
# Shared Backend Capabilities
# ==========================================================

class BaseBackend(ABC):
    """
    Common backend contract.

    All backends MUST:
    - Execute Lua scripts atomically
    - Perform exactly one backend round-trip
    - Return raw Lua results without mutation
    """

    # ------------------------------------------------------
    # Required
    # ------------------------------------------------------

    @abstractmethod
    def execute(
        self,
        script: str,
        keys: Sequence[str],
        args: Sequence[Any],
    ) -> List[Any]:
        """
        Execute a Lua script atomically.

        Args:
            script: Lua script source
            keys: Redis keys (KEYS)
            args: Script arguments (ARGV)

        Returns:
            Raw Lua return value as a list
        """
        raise NotImplementedError

    # ------------------------------------------------------
    # Optional (but recommended for enterprise)
    # ------------------------------------------------------

    def health_check(self) -> bool:
        """
        Check backend availability.

        Default implementation assumes healthy.
        Backends managing network connections SHOULD override.
        """
        return True

    def get_time(self) -> float:
        """
        Optional backend time source.

        Used for debugging / observability.
        Default implementation raises NotImplementedError.
        """
        raise NotImplementedError(
            "Backend does not implement get_time()"
        )

    def close(self) -> None:
        """
        Gracefully close backend resources.

        Default implementation is a no-op.
        """
        return None


# ==========================================================
# Synchronous Backend
# ==========================================================

class Backend(BaseBackend):
    """
    Synchronous backend interface.
    """
    pass


# ==========================================================
# Asynchronous Backend
# ==========================================================

class AsyncBackend(ABC):
    """
    Asynchronous backend interface.

    Async backends MUST:
    - Execute scripts atomically
    - Perform exactly one round-trip
    - Return raw Lua results
    """

    @abstractmethod
    async def execute(
        self,
        script: str,
        keys: Sequence[str],
        args: Sequence[Any],
    ) -> List[Any]:
        raise NotImplementedError

    async def health_check(self) -> bool:
        """
        Async health check.
        Default assumes healthy.
        """
        return True

    async def get_time(self) -> float:
        """
        Optional backend time source (async).
        """
        raise NotImplementedError(
            "Async backend does not implement get_time()"
        )

    async def close(self) -> None:
        """
        Gracefully close backend resources.
        Default no-op.
        """
        return None