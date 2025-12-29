import pytest
from distributed_rate_limiter import RateLimiter, ConfigurationError


def test_empty_identity_rejected(redis_url):
    limiter = RateLimiter(
        rate=1,
        per=10,
        redis_url=redis_url,
    )

    with pytest.raises(ConfigurationError):
        limiter.allow("")


def test_non_string_identity_rejected(redis_url):
    limiter = RateLimiter(
        rate=1,
        per=10,
        redis_url=redis_url,
    )

    with pytest.raises(ConfigurationError):
        limiter.allow(123)  # type: ignore


def test_very_long_identity_rejected(redis_url):
    limiter = RateLimiter(
        rate=1,
        per=10,
        redis_url=redis_url,
    )

    with pytest.raises(ConfigurationError):
        limiter.allow("x" * 5000)
