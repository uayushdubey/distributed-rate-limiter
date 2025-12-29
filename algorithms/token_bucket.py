from typing import List

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

    def args(self) -> List:
        return [self.rate, self.per]

    def lua_script(self) -> str:
        """
        Atomic Redis Lua script implementing token bucket.

        Uses Redis TIME to avoid clock skew.
        """
        return """
        local key = KEYS[1]
        local rate = tonumber(ARGV[1])
        local per = tonumber(ARGV[2])

        -- Redis server time (seconds)
        local now = redis.call("TIME")[1]

        -- Fetch existing state
        local data = redis.call("HMGET", key, "tokens", "timestamp")
        local tokens = tonumber(data[1])
        local last = tonumber(data[2])

        -- Initialize bucket if missing
        if tokens == nil then
            tokens = rate
            last = now
        end

        -- Refill tokens
        local delta = math.max(0, now - last)
        local refill = (delta * rate) / per
        tokens = math.min(rate, tokens + refill)

        local allowed = 0
        if tokens >= 1 then
            allowed = 1
            tokens = tokens - 1
        end

        -- Persist updated state
        redis.call("HMSET", key, "tokens", tokens, "timestamp", now)
        redis.call("EXPIRE", key, math.ceil(per * 2))

        -- Calculate reset timestamp
        local missing = rate - tokens
        local reset = now + math.ceil((missing * per) / rate)

        return { allowed, tokens, reset }
        """
