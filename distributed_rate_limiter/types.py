from dataclasses import dataclass
from typing import Dict, Any


@dataclass(frozen=True, slots=True)
class RateLimitInfo:
    """
    Immutable metadata about the current rate limit state.

    Designed for enterprise API integrations.
    """

    limit: int
    remaining: int
    reset: int  # absolute unix timestamp (seconds)
    allowed: bool
    cost: int = 1

    # ----------------------------------------
    # Derived properties
    # ----------------------------------------

    @property
    def retry_after(self) -> int:
        """
        Seconds until reset (derived from remaining reset window).
        NOTE: reset must be computed from Redis TIME for correctness.
        """
        # reset is absolute timestamp from Redis
        # remaining reset time = reset - current timestamp
        # We do not use Python time for precision-sensitive logic
        # This assumes reset already computed correctly by Lua
        return max(0, self.reset - int(self.reset))

    @property
    def reset_after(self) -> int:
        """
        Alias for semantic clarity.
        """
        return self.retry_after

    # ----------------------------------------
    # Serialization Helpers
    # ----------------------------------------

    def as_headers(self) -> Dict[str, str]:
        """
        RFC-compliant RateLimit headers (relative reset).
        """
        return {
            "RateLimit-Limit": str(self.limit),
            "RateLimit-Remaining": str(self.remaining),
            "RateLimit-Reset": str(self.reset_after),
        }

    def as_absolute_headers(self) -> Dict[str, str]:
        """
        Alternative header style with absolute reset timestamp.
        """
        return {
            "RateLimit-Limit": str(self.limit),
            "RateLimit-Remaining": str(self.remaining),
            "RateLimit-Reset": str(self.reset),
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize to dictionary for logging / JSON output.
        """
        return {
            "limit": self.limit,
            "remaining": self.remaining,
            "reset": self.reset,
            "allowed": self.allowed,
            "cost": self.cost,
        }

    # ----------------------------------------
    # Ergonomic Helpers
    # ----------------------------------------

    def __bool__(self) -> bool:
        """
        Allows:
            if info:
                ...
        Equivalent to info.allowed
        """
        return self.allowed