from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RateLimitInfo:
    """
    Immutable metadata about the current rate limit state.
    """
    limit: int
    remaining: int
    reset: int  # unix timestamp (seconds)
