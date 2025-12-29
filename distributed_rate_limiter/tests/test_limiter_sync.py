from distributed_rate_limiter import RateLimiter


def test_sync_allows_within_limit(redis_url):
    limiter = RateLimiter(
        rate=3,
        per=10,
        redis_url=redis_url,
    )

    for _ in range(3):
        allowed, info = limiter.allow("user-sync")
        assert allowed is True
        assert info.remaining >= 0

    allowed, info = limiter.allow("user-sync")
    assert allowed is False
