from typing import Callable, Optional


class FastAPIRateLimiter:
    """
    Enterprise-grade FastAPI middleware for distributed-rate-limiter.

    Requirements:
    - fastapi installed
    - RateLimiter(async_mode=True)
    """

    def __init__(
        self,
        limiter,
        *,
        key_func: Optional[Callable] = None,
        cost_func: Optional[Callable] = None,
        status_code: int = 429,
        trust_proxy: bool = False,
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
        self.cost_func = cost_func
        self.status_code = status_code
        self.trust_proxy = trust_proxy

    # -----------------------------------------------------
    # Identity Resolution
    # -----------------------------------------------------

    def _resolve_identity(self, request):
        if self.key_func:
            return self.key_func(request)

        if self.trust_proxy:
            forwarded = request.headers.get("x-forwarded-for")
            if forwarded:
                return forwarded.split(",")[0].strip()

        return request.client.host if request.client else None

    # -----------------------------------------------------
    # Middleware Entry
    # -----------------------------------------------------

    async def __call__(self, request, call_next):

        identity = self._resolve_identity(request)

        if not identity:
            return self.JSONResponse(
                status_code=self.status_code,
                content={"detail": "Rate limit identity missing"},
            )

        cost = 1
        if self.cost_func:
            try:
                cost = int(self.cost_func(request))
            except Exception:
                cost = 1

        allowed, info = await self.limiter.allow_async(
            identity,
            cost=cost,
        )

        # --------------------------------------------
        # Blocked
        # --------------------------------------------
        if not allowed:
            headers = {}

            if info:
                headers.update(info.as_headers())
                headers["Retry-After"] = str(info.retry_after)

            return self.JSONResponse(
                status_code=self.status_code,
                content={"detail": "Rate limit exceeded"},
                headers=headers,
            )

        # --------------------------------------------
        # Allowed
        # --------------------------------------------
        response = await call_next(request)

        if info:
            response.headers.update(info.as_headers())

        return response