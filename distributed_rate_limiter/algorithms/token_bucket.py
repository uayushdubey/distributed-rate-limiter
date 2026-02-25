from __future__ import annotations

from typing import Sequence
from .base import RateLimitAlgorithm


class TokenBucket(RateLimitAlgorithm):
    """
    Enterprise-grade Token Bucket rate limiting algorithm.

    Features:
    - Atomic correctness under concurrency
    - Weighted token consumption
    - Configurable burst capacity
    - Redis TIME based (clock-skew resistant)
    - Reduced write amplification
    """

    name = "token_bucket"

    def __init__(self, rate: int, per: int, burst: int | None = None):
        self.rate = rate
        self.per = per
        self.burst = burst if burst is not None else rate

    def args(self) -> Sequence:
        return [self.rate, self.per, self.burst]

    def lua_script(self) -> str:
        return """
        local key = KEYS[1]

        local rate = tonumber(ARGV[1])
        local per = tonumber(ARGV[2])
        local capacity = tonumber(ARGV[3])
        local cost = tonumber(ARGV[4]) or 1

        -- Redis server time
        local time = redis.call("TIME")
        local now = tonumber(time[1]) + (tonumber(time[2]) / 1000000)

        -- Fetch existing state
        local data = redis.call("HMGET", key, "tokens", "last_refill")
        local tokens = tonumber(data[1])
        local last_refill = tonumber(data[2])

        -- Initialize if missing
        if tokens == nil then
            tokens = capacity
            last_refill = now
        end

        -- Refill logic
        local delta = math.max(0, now - last_refill)
        local refill = (delta * rate) / per
        tokens = math.min(capacity, tokens + refill)

        local allowed = 0

        if tokens >= cost then
            allowed = 1
            tokens = tokens - cost
        end

        -- Clamp tokens to avoid float drift
        if tokens < 0 then
            tokens = 0
        end

        -- Persist updated state
        redis.call(
            "HMSET",
            key,
            "tokens", tokens,
            "last_refill", now
        )

        -- Set expiry only relative to idle timeout
        redis.call("PEXPIRE", key, math.ceil(per * 2000))

        -- Compute reset timestamp
        local missing = capacity - tokens
        local reset = math.ceil(now + (missing * per) / rate)

        return { allowed, tokens, reset }
        """