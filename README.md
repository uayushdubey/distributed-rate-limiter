# distributed-rate-limiter

A production-grade, Redis-backed, horizontally scalable traffic governance library for Python.

Designed for high-concurrency APIs, SaaS platforms, ML inference systems, and distributed applications.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/distributed-rate-limiter.svg)](https://badge.fury.io/py/distributed-rate-limiter)

---

## Why distributed-rate-limiter?

- Deterministic under concurrency (Lua atomicity)
- Redis TIME-based (clock-skew resistant)
- Cost-aware (weighted tokens)
- Burst control
- RFC-compliant RateLimit headers
- Sync + Async support
- Fail-open / Fail-closed modes
- No in-memory state
- Enterprise-ready architecture

---

# Installation

```bash
pip install distributed-rate-limiter
Optional extras
pip install distributed-rate-limiter[async]
pip install distributed-rate-limiter[fastapi]
pip install distributed-rate-limiter[flask]
pip install distributed-rate-limiter[all]
Quick Start
Basic Usage
from distributed_rate_limiter import RateLimiter

limiter = RateLimiter(
    redis_url="redis://localhost:6379",
    rate=100,
    per=60,
    burst=200,
    namespace="myapp"
)

allowed, info = limiter.allow("user:123")

if allowed:
    print("Allowed")
    print("Remaining:", info.remaining)
else:
    print("Blocked")
    print("Retry after:", info.retry_after)
Weighted Token Consumption (Cost-Based Throttling)

Useful for:

LLM token usage

File size-based throttling

Tier-based billing

GPU workload shaping

allowed, info = limiter.allow(
    "user:123",
    cost=5
)
Async Usage
limiter = RateLimiter(
    redis_url="redis://localhost:6379",
    rate=100,
    per=60,
    async_mode=True
)

allowed, info = await limiter.allow_async("user:123")
FastAPI Integration
from fastapi import FastAPI
from distributed_rate_limiter.middleware import FastAPIRateLimiter
from distributed_rate_limiter import RateLimiter

app = FastAPI()

limiter = RateLimiter(
    redis_url="redis://localhost:6379",
    rate=100,
    per=60,
    async_mode=True
)

app.middleware("http")(
    FastAPIRateLimiter(
        limiter,
        trust_proxy=True
    )
)

Automatically sets:

RateLimit-Limit

RateLimit-Remaining

RateLimit-Reset

Retry-After (on 429)

Flask Integration
from flask import Flask
from distributed_rate_limiter.decorators import rate_limit
from distributed_rate_limiter import RateLimiter

app = Flask(__name__)

limiter = RateLimiter(
    redis_url="redis://localhost:6379",
    rate=100,
    per=60
)

@app.route("/api")
@rate_limit(limiter, trust_proxy=True)
def api():
    return {"ok": True}
Algorithm
Token Bucket (Default)

Smooth rate limiting with burst support.

RateLimiter(
    redis_url="redis://localhost:6379",
    rate=100,
    per=60,
    burst=200
)
Characteristics

O(1) Redis operations

O(1) memory per identity

Weighted tokens supported

Atomic Lua execution

Redis TIME-based refill

Auto-expiring keys

Configuration
Failure Modes
RateLimiter(fail_strategy="open")   # default
RateLimiter(fail_strategy="closed")
Namespacing
RateLimiter(namespace="api")
RateLimiter(namespace="auth")

Redis key format:

<namespace>:<algorithm>:<sha256(identity)>
Observability

Hooks:

def on_allow(identity, info):
    print(info.to_dict())

def on_block(identity, info):
    print("Blocked:", info.retry_after)

def on_error(exc):
    print("Backend error:", exc)

RateLimiter(
    redis_url="redis://localhost:6379",
    rate=100,
    per=60,
    on_allow=on_allow,
    on_block=on_block,
    on_error=on_error
)
Security

SHA-256 identity hashing

No raw identities stored

No PII inspection

No in-memory fallback

Configurable failure modes

Performance

Single Redis round-trip

Atomic Lua execution

Stateless application layer

Horizontally scalable

O(1) operations per request

Architecture
Application
    ↓
RateLimiter
    ↓
Algorithm (Token Bucket)
    ↓
Redis Backend (Lua)
    ↓
Redis
Design Principles

Redis is the single source of truth

Deterministic distributed behavior

No in-memory fallback

Cost-aware traffic governance

Clean abstraction layers

Backward-compatible API evolution

Roadmap

Sliding Window algorithm

Concurrency limiter (ML/GPU workloads)

Prometheus metrics integration

OpenTelemetry tracing

Sharded buckets (hot-key scaling)

Standalone service mode

FAQ
Why Redis?

Redis provides atomic Lua execution, essential for correctness under distributed concurrency.

Why no in-memory fallback?

In-memory fallback breaks horizontal scaling correctness.

Multi-region support?

Deploy independent Redis per region. Global synchronization is intentionally not handled.

License

MIT
