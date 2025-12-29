import pytest
from distributed_rate_limiter import RateLimiter


@pytest.mark.asyncio
async def test_async_allows_within_limit(redis_url):
    limiter = RateLimiter(
        rate=2,
        per=10,
        redis_url=redis_url,
        async_mode=True,
    )

    allowed, _ = await limiter.allow_async("user-async")
    assert allowed is True

    allowed, _ = await limiter.allow_async("user-async")
    assert allowed is True

    allowed, _ = await limiter.allow_async("user-async")
    assert allowed is False
