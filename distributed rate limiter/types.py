from dataclasses import dataclass


@dataclass(frozen=True)
class RateLimitInfo:
    """
    Immutable metadata about the current rate limit state.

    Attributes:
        limit: Maximum number of allowed requests in the window
        remaining: Remaining requests in the current window
        reset: Unix timestamp (seconds) when the bucket fully resets
    """
    limit: int
    remaining: int
    reset: int
