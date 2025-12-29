from functools import wraps
from typing import Callable, Optional

import flask


def rate_limit(
    limiter,
    *,
    key_func: Optional[Callable] = None,
    status_code: int = 429,
):
    """
    Flask decorator for rate limiting routes.

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

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Resolve identity
            if key_func:
                identity = key_func()
            else:
                identity = flask.request.remote_addr

            allowed, info = limiter.allow(identity)

            if not allowed:
                flask.abort(status_code)

            # Store info for optional use in view
            if info:
                flask.g.rate_limit = info

            return fn(*args, **kwargs)

        return wrapper

    return decorator
