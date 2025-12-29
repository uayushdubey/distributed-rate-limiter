from typing import Callable, Optional


class FastAPIRateLimiter:
    """
    FastAPI middleware for distributed-rate-limiter.

    This middleware requires:
    - fastapi
    - RateLimiter(async_mode=True)
    """

    def __init__(
        self,
        limiter,
        *,
        key_func: Optional[Callable] = None,
        status_code: int = 429,
    ):
        try:
            import fastapi
            from fastapi.responses import JSONResponse
        except ImportError as exc:
            raise RuntimeError(
                "FastAPIRateLimiter requires fastapi to be installed"
            ) from exc

        if not limiter.async_mode:
            raise RuntimeError(
                "FastAPIRateLimiter requires RateLimiter(async_mode=True)"
            )

        self.fastapi = fastapi
        self.JSONResponse = JSONResponse
        self.limiter = limiter
        self.key_func = key_func
        self.status_code = status_code

    async def __call__(self, request, call_next):
        # Resolve identity
        if self.key_func:
            identity = self.key_func(request)
        else:
            identity = request.client.host if request.client else None

        if not identity:
            return self.JSONResponse(
                status_code=self.status_code,
                content={"detail": "Rate limit identity missing"},
            )

        allowed, info = await self.limiter.allow_async(identity)

        if not allowed:
            return self.JSONResponse(
                status_code=self.status_code,
                content={"detail": "Rate limit exceeded"},
            )

        response = await call_next(request)

        if info:
            response.headers["X-RateLimit-Limit"] = str(info.limit)
            response.headers["X-RateLimit-Remaining"] = str(info.remaining)
            response.headers["X-RateLimit-Reset"] = str(info.reset)

        return response
