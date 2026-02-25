class RateLimiterError(Exception):
    """
    Base exception for all rate limiter related errors.
    """

    pass


# ==========================================================
# Configuration Errors
# ==========================================================

class ConfigurationError(RateLimiterError):
    """
    Raised when the rate limiter is misconfigured.
    """

    pass


class IdentityError(RateLimiterError):
    """
    Raised when an invalid identity is provided.
    """

    pass


# ==========================================================
# Backend Errors
# ==========================================================

class BackendError(RateLimiterError):
    """
    Base class for backend-related failures.
    """

    pass


class BackendUnavailable(BackendError):
    """
    Raised when backend is unavailable and fail_strategy='closed'.
    """

    pass


class BackendExecutionError(BackendError):
    """
    Raised when a backend execution fails unexpectedly.
    """

    pass


# ==========================================================
# Algorithm Errors
# ==========================================================

class AlgorithmError(RateLimiterError):
    """
    Raised when an algorithm fails or returns invalid data.
    """

    pass