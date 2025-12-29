from typing import Sequence

from .base import RateLimitAlgorithm


class TokenBucket(RateLimitAlgorithm):
    """
    Token Bucket rate limiting algorithm.

    Guarantees:
    - Atomic correctness under concurrency
    - Smooth refill
    - Burst control
    """

    name = "token_bucket"

    def __init__(self, rate: int, per: int):
        self.rate = rate
        self.per = per

    def args(self) -> Sequence:
        return [self.rate, self.per]

    def lua_script(self) -> str:
        """
        Atomic Redis Lua script implementing token bucket.

        Uses Redis TIME with sub-second precision
        to avoid clock skew and improve accuracy.
        """
        return """
        local key = KEYS[1]
        local rate = tonumber(ARGV[1])
        local per = tonumber(ARGV[2])

        -- Redis server time (seconds + microseconds)
        local time = redis.call("TIME")
        local now = tonumber(time[1]) + (tonumber(time[2]) / 1000000)

        -- Fetch existing state
        local data = redis.call("HMGET", key, "tokens", "last_refill")
        local tokens = tonumber(data[1])
        local last_refill = tonumber(data[2])

        -- Initialize bucket if missing
        if tokens == nil then
            tokens = rate
            last_refill = now
        end

        -- Refill tokens
        local delta = math.max(0, now - last_refill)
        local refill = (delta * rate) / per
        tokens = math.min(rate, tokens + refill)

        local allowed = 0
        if tokens >= 1 then
            allowed = 1
            tokens = tokens - 1
        end

        -- Persist updated state
        redis.call(
            "HMSET",
            key,
            "tokens", tokens,
            "last_refill", now
        )
        redis.call("EXPIRE", key, math.ceil(per * 2))

        -- Calculate reset timestamp (seconds)
        local missing = rate - tokens
        local reset = math.ceil(now + (missing * per) / rate)

        return { allowed, tokens, reset }
        """
