class RateLimiterError(Exception):
    """
    Base exception for all rate limiter related errors.
    """


class ConfigurationError(RateLimiterError):
    """
    Raised when the rate limiter is misconfigured.
    """


class BackendUnavailable(RateLimiterError):
    """
    Raised when Redis is unavailable and fail_strategy='closed'.
    """
