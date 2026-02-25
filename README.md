# distributed-rate-limiter

Production-grade, Redis-backed rate limiting for high-concurrency distributed systems.

`distributed-rate-limiter` is a horizontally scalable, atomic, and stateless rate limiting library built for modern API infrastructure. Designed for SaaS platforms, ML inference systems, and distributed microservices, it guarantees consistency across nodes while maintaining O(1) Redis operations per request.

It is engineered for production environments where correctness, scalability, and operational predictability are non-negotiable.

---

## Why distributed-rate-limiter

- Redis-backed single source of truth
- Lua-scripted atomic operations
- Redis TIME usage to eliminate clock skew
- Fully stateless Python workers
- Sync and async support
- Cost-based (weighted) throttling
- Burst capacity control
- Fail-open and fail-closed strategies
- RFC-compliant `RateLimit-*` headers
- FastAPI middleware
- Flask decorator
- SHA-256 identity hashing
- No in-memory fallback
- O(1) Redis round-trip per request

---

## Installation

```bash
pip install distributed-rate-limiter
```
Requires Redis 6.0+.

# Quick Start

```bash
from distributed_rate_limiter import RateLimiter

limiter = RateLimiter(
    redis_url="redis://localhost:6379/0",
    rate=100,
    per=60,
)

allowed, info = limiter.allow("user_123")

if not allowed:
    print("Retry after:", info.retry_after)
```
# Cost-Based Throttling (Weighted Tokens)

Consume more than one token per request.

```bash
allowed, info = limiter.allow("user_123", cost=5)

if allowed:
    print("Remaining:", info.remaining)
else:
    print("Retry after:", info.retry_after)
```
This is ideal for:

1. ML inference workloads

2. Variable-cost API endpoints

3. Multi-tenant SaaS billing tiers

# Async Usage

```bash
from distributed_rate_limiter import RateLimiter

limiter = RateLimiter(
    redis_url="redis://localhost:6379/0",
    rate=1000,
    per=60,
    async_mode=True,
)
allowed, info = await limiter.allow_async("user_123", cost=2)
```
# FastAPI Integration
```bash
from fastapi import FastAPI
from distributed_rate_limiter import RateLimiter
from distributed_rate_limiter.fastapi import FastAPIRateLimiter

limiter = RateLimiter(
    redis_url="redis://localhost:6379/0",
    rate=100,
    per=60,
)

app = FastAPI()
app.add_middleware(FastAPIRateLimiter, limiter=limiter, trust_proxy=True)
```
Automatically injects RFC-compliant headers and enforces limits before route execution.

# Flask Integration

```bash
from flask import Flask
from distributed_rate_limiter import RateLimiter
from distributed_rate_limiter.flask import rate_limit

app = Flask(__name__)

limiter = RateLimiter(
    redis_url="redis://localhost:6379/0",
    rate=50,
    per=60,
)

@app.route("/api")
@rate_limit(limiter, trust_proxy=True)
def my_route():
    return {"status": "ok"}
```
# Algorithm
Token Bucket (Distributed)

The limiter implements a Redis-backed Token Bucket algorithm.

1. rate: maximum tokens per window
2. per: window size in seconds
3. burst: optional bucket capacity override
4. Tokens refill continuously
5. Atomic Lua script ensures consistency
6. Redis TIME prevents multi-node clock drift

Each request: 

1. Fetches current Redis time
2. Calculates token refill
3. Deducts cost
4. Returns updated state
5. Computes retry-after if denied

All in a single Lua execution (O(1) complexity).

# Configuration
```bash
RateLimiter(
    redis_url: str,
    rate: int,
    per: int,
    burst: Optional[int] = None,
    namespace: str = "default",
    fail_strategy: str = "open",
    async_mode: bool = False,
)
```

# Parameters
| Parameter       | Description                            |
| --------------- | -------------------------------------- |
| `redis_url`     | Redis connection string                |
| `rate`          | Tokens per window                      |
| `per`           | Window size (seconds)                  |
| `burst`         | Max bucket capacity (defaults to rate) |
| `namespace`     | Logical isolation prefix               |
| `fail_strategy` | `"open"` or `"closed"`                 |
| `async_mode`    | Enables async Redis client             |

Observability

RateLimitInfo exposes:

1. limit
2. remaining
3. reset
4. allowed
5. cost
6. retry_after
7. as_headers()

Example:
```bash
headers = info.as_headers()
```
You can:

1. Export remaining and retry_after to metrics
2. Attach headers to structured logs
3. Emit denial counters to Prometheus
4. Track tenant-level consumption

The library does not hide internal state and is designed for transparent integration into observability pipelines.

# Security

1. SHA-256 identity hashing (no raw identity storage in Redis)
2. Namespaced keys to avoid collisions
3. No in-memory fallback (prevents split-brain inconsistencies)
4. Atomic Lua execution eliminates race conditions
5. Fail-open or fail-closed behavior configurable
6. Safe behind reverse proxies (trust_proxy=True)
7. Designed for zero-trust distributed deployments.

# Performance

1. Single Redis round-trip per request
2. O(1) operations
3. Constant memory per identity
4. No polling
5. No background workers
6. No synchronization across app instances

Benchmarks under high concurrency demonstrate linear scalability bounded only by Redis throughput.

Recommended production setup:

1. Dedicated Redis instance or cluster
2. Connection pooling enabled
3. TCP keepalive
4. Redis persistence tuned to workload

# Architecture

                   +----------------------+
                   |  Client Requests     |
                   +----------+-----------+
                              |
                              v
                   +----------------------+
                   |  API Instances       |
                   |  (Stateless Python)  |
                   +----------+-----------+
                              |
                              v
                   +----------------------+
                   |  Redis               |
                   |  - Lua Script        |
                   |  - Token Buckets     |
                   |  - Redis TIME        |
                   +----------------------+

Multiple API instances share the same Redis state, ensuring global rate enforcement across nodes.
