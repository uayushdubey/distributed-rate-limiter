import pytest
from distributed_rate_limiter import RateLimiter, BackendUnavailable


def test_fail_open_allows_on_redis_error():
    limiter = RateLimiter(
        rate=1,
        per=1,
        redis_url="redis://localhost:9999/0",  # invalid
        fail_strategy="open",
    )

    allowed, info = limiter.allow("user")
    assert allowed is True
    assert info is None


def test_fail_closed_blocks_on_redis_error():
    limiter = RateLimiter(
        rate=1,
        per=1,
        redis_url="redis://localhost:9999/0",  # invalid
        fail_strategy="closed",
    )

    with pytest.raises(BackendUnavailable):
        limiter.allow("user")
