from functools import wraps
from typing import Callable, Optional

import flask


def rate_limit(
    limiter,
    *,
    key_func: Optional[Callable] = None,
    cost_func: Optional[Callable] = None,
    status_code: int = 429,
    trust_proxy: bool = False,
):
    """
    Enterprise-grade Flask decorator for rate limiting routes.

    Example:
        @app.route("/api")
        @rate_limit(limiter)
        def handler():
            ...
    """

    if limiter.async_mode:
        raise RuntimeError(
            "Flask rate limiting requires RateLimiter(async_mode=False)"
        )

    def resolve_identity():
        if key_func:
            return key_func()

        if trust_proxy:
            forwarded = flask.request.headers.get("X-Forwarded-For")
            if forwarded:
                return forwarded.split(",")[0].strip()

        return flask.request.remote_addr

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):

            identity = resolve_identity()

            if not identity:
                flask.abort(status_code)

            cost = 1
            if cost_func:
                try:
                    cost = int(cost_func())
                except Exception:
                    cost = 1

            allowed, info = limiter.allow(identity, cost=cost)

            # ----------------------------------------
            # Blocked
            # ----------------------------------------
            if not allowed:
                response = flask.make_response(
                    {"detail": "Rate limit exceeded"},
                    status_code,
                )

                if info:
                    response.headers.update(info.as_headers())
                    response.headers["Retry-After"] = str(
                        info.retry_after
                    )

                return response

            # ----------------------------------------
            # Allowed
            # ----------------------------------------
            response = fn(*args, **kwargs)

            # Normalize response object
            response = flask.make_response(response)

            if info:
                response.headers.update(info.as_headers())
                flask.g.rate_limit = info

            return response

        return wrapper

    return decorator