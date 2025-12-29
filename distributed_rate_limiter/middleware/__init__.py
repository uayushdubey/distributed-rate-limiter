"""
Framework integrations for distributed-rate-limiter.

These adapters are OPTIONAL and do not affect core behavior.
"""

from .fastapi import FastAPIRateLimiter
from .flask import rate_limit

__all__ = (
    "FastAPIRateLimiter",
    "rate_limit",
)
