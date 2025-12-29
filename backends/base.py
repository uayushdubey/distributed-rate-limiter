from abc import ABC, abstractmethod
from typing import Any, List, Sequence


class Backend(ABC):
    """
    Synchronous backend interface for executing Lua scripts.

    Implementations MUST:
    - Execute the script atomically
    - Perform exactly one backend round-trip
    - Return raw Lua results without mutation
    """

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


class AsyncBackend(ABC):
    """
    Asynchronous backend interface for executing Lua scripts.
    """

    @abstractmethod
    async def execute(
        self,
        script: str,
        keys: Sequence[str],
        args: Sequence[Any],
    ) -> List[Any]:
        raise NotImplementedError
