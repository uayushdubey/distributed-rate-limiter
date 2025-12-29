from abc import ABC, abstractmethod
from typing import List, Sequence


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

    @abstractmethod
    def lua_script(self) -> str:
        """
        Return the Lua script implementing the algorithm.

        The script MUST:
        - Be atomic
        - Use Redis server time
        - Return a fixed result structure
        """
        raise NotImplementedError

    @abstractmethod
    def args(self) -> List:
        """
        Return arguments passed to the Lua script (ARGV).
        """
        raise NotImplementedError

    def redis_key_suffix(self) -> str:
        """
        Short identifier used in Redis key namespacing.
        """
        return self.name
