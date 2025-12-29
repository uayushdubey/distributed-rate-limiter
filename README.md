# distributed-rate-limiter

A production-grade, Redis-backed, horizontally scalable Python rate limiting library.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/distributed-rate-limiter.svg)](https://badge.fury.io/py/distributed-rate-limiter)

## Features

- **Library-first**: Self-hosted, open-source, no SaaS dependencies
- **Framework-agnostic**: Works with FastAPI, Flask, or any Python application
- **Horizontally scalable**: Stateless design with Redis as the single source of truth
- **Atomic operations**: Lua scripts ensure correctness under concurrency
- **Sync + Async**: Native support for both synchronous and asynchronous code
- **Security-first**: Hashed identities, no PII storage, configurable failure modes
- **Zero dependencies**: Core library only requires Redis

## Installation

```bash
pip install distributed-rate-limiter
```

### Optional dependencies

```bash
# For async support
pip install distributed-rate-limiter[async]

# For FastAPI integration
pip install distributed-rate-limiter[fastapi]

# For Flask integration
pip install distributed-rate-limiter[flask]

# Install all extras
pip install distributed-rate-limiter[all]
```

## Quick Start

### Basic Usage

```python
from distributed_rate_limiter import RateLimiter

# Initialize the rate limiter
limiter = RateLimiter(
    redis_url="redis://localhost:6379",
    rate=100,           # 100 requests
    period=60,          # per 60 seconds
    namespace="myapp"
)

# Check if request is allowed
identity = "user:12345"  # or IP address, API key, etc.
result = limiter.allow(identity)

if result.allowed:
    print(f"Request allowed. Remaining: {result.remaining}")
else:
    print(f"Rate limited. Retry after: {result.reset_timestamp}")
```

### Async Usage

```python
from distributed_rate_limiter import AsyncRateLimiter

limiter = AsyncRateLimiter(
    redis_url="redis://localhost:6379",
    rate=100,
    period=60
)

result = await limiter.allow_async("user:12345")
```

### FastAPI Integration

```python
from fastapi import FastAPI, Request, HTTPException
from distributed_rate_limiter.middleware import FastAPIRateLimitMiddleware

app = FastAPI()

app.add_middleware(
    FastAPIRateLimitMiddleware,
    redis_url="redis://localhost:6379",
    rate=100,
    period=60,
    identity_extractor=lambda request: request.client.host
)

@app.get("/api/data")
async def get_data():
    return {"message": "Hello, World!"}
```

### Flask Integration

```python
from flask import Flask
from distributed_rate_limiter.decorators import rate_limit

app = Flask(__name__)

@app.route("/api/data")
@rate_limit(
    redis_url="redis://localhost:6379",
    rate=100,
    period=60,
    identity_extractor=lambda: request.remote_addr
)
def get_data():
    return {"message": "Hello, World!"}
```

## Algorithms

### Token Bucket (Default)

The Token Bucket algorithm provides smooth rate limiting with burst control.

```python
limiter = RateLimiter(
    redis_url="redis://localhost:6379",
    algorithm="token_bucket",  # default
    rate=100,
    period=60,
    burst=20  # allow bursts up to 20 requests
)
```

**Characteristics:**
- O(1) Redis operations
- O(1) memory per identity
- Smooth token refill
- Configurable burst capacity
- Clock-skew resistant (uses Redis TIME)

### Sliding Window (Coming Soon)

A sliding window algorithm will be available in a future release.

## Configuration

### Redis Connection

```python
# Basic connection
limiter = RateLimiter(redis_url="redis://localhost:6379")

# With password
limiter = RateLimiter(redis_url="redis://:password@localhost:6379")

# Redis Cluster
limiter = RateLimiter(redis_url="redis://localhost:6379", cluster_mode=True)

# Custom Redis client
import redis
client = redis.Redis(host="localhost", port=6379, db=0)
limiter = RateLimiter(redis_client=client)
```

### Failure Modes

Configure how the limiter behaves when Redis is unavailable:

```python
# Fail open: allow traffic when Redis is down (default)
limiter = RateLimiter(
    redis_url="redis://localhost:6379",
    fail_strategy="open"
)

# Fail closed: block traffic when Redis is down
limiter = RateLimiter(
    redis_url="redis://localhost:6379",
    fail_strategy="closed"
)
```

### Namespacing

Use namespaces to isolate rate limits for different services or endpoints:

```python
api_limiter = RateLimiter(
    redis_url="redis://localhost:6379",
    namespace="api"
)

auth_limiter = RateLimiter(
    redis_url="redis://localhost:6379",
    namespace="auth",
    rate=10,
    period=60
)
```

## Observability

Add hooks to monitor rate limiting behavior:

```python
def on_allow(identity: str, info: dict):
    print(f"Allowed: {identity}, remaining: {info['remaining']}")

def on_block(identity: str, info: dict):
    print(f"Blocked: {identity}, reset at: {info['reset_timestamp']}")

def on_error(exception: Exception):
    print(f"Error: {exception}")

limiter = RateLimiter(
    redis_url="redis://localhost:6379",
    on_allow=on_allow,
    on_block=on_block,
    on_error=on_error
)
```

## Security

### Identity Hashing

All identities are SHA-256 hashed before being stored in Redis:

```python
# Raw identity never stored in Redis
identity = "user@example.com"  # Hashed to SHA-256
result = limiter.allow(identity)
```

### No PII Storage

- Identities are hashed with SHA-256
- No personally identifiable information stored in Redis
- No request body inspection
- No secrets logged or stored

### Redis Key Format

```
<namespace>:<algorithm>:<sha256(identity)>
```

Example:
```
myapp:token_bucket:a7b3c9d1e2f4...
```

## Performance

- **O(1) Redis operations** per request
- **O(1) memory** per unique identity
- **Atomic Lua scripts** prevent race conditions
- **Auto-expiring keys** minimize memory usage
- **Horizontally scalable** with stateless Python processes

## Architecture

```
┌─────────────────┐
│  Your App       │
│  (Sync/Async)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  RateLimiter    │
│  Public API     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Algorithm      │
│  (Token Bucket) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Redis Backend  │
│  (Lua Scripts)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Redis Server   │
│  (Single Truth) │
└─────────────────┘
```

## Design Principles

1. **Redis is the single source of truth**: No in-memory state in Python processes
2. **Atomic operations**: All state changes use Lua scripts
3. **Clock-skew resistant**: Uses Redis TIME, not Python time
4. **Fail-fast**: No retries, no backoff, clear failure modes
5. **Framework-agnostic**: Core library has zero framework dependencies
6. **API stability**: Backward compatibility is a priority

## Testing

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=distributed_rate_limiter

# Run tests against Redis
docker run -d -p 6379:6379 redis:7-alpine
pytest
```

## Requirements

- Python 3.9+
- Redis 5.0+ (self-hosted)
- redis-py 4.0+

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
git clone https://github.com/yourusername/distributed-rate-limiter.git
cd distributed-rate-limiter
pip install -e ".[dev]"
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Roadmap

- [x] Token Bucket algorithm
- [x] Sync and async support
- [x] FastAPI middleware
- [x] Flask decorators
- [ ] Sliding Window algorithm
- [ ] Prometheus metrics integration
- [ ] OpenTelemetry tracing support
- [ ] Rate limit headers (RateLimit-* RFC)

## FAQ

### Why Redis only?

Redis provides atomic operations via Lua scripts, which is essential for correctness under horizontal scaling. We intentionally keep the backend simple and reliable.

### Why no in-memory fallback?

In-memory state breaks horizontal scaling correctness. When Redis is unavailable, you should either fail open (allow traffic) or fail closed (block traffic), not fall back to incorrect rate limiting.

### Can I use this with Redis Cluster?

Yes, but be aware that Lua scripts must operate on a single node. Use consistent hashing or the `{hash_tag}` feature to ensure related keys are on the same node.

### Does this support distributed tracing?

Not built-in, but you can add tracing via the observability hooks (`on_allow`, `on_block`, `on_error`).

### How do I handle multi-region deployments?

Deploy separate Redis instances per region and configure your rate limiter accordingly. This library does not handle cross-region synchronization.

## Support

- **Issues**: [GitHub Issues](https://github.com/uayushdubey/distributed-rate-limiter/issues)
- **Discussions**: [GitHub Discussions](https://github.com/uayushdubey/distributed-rate-limiter/discussions)
- **Security**: Report security issues to work.ayushkumardubey@gmail.com

## Acknowledgments

Built with inspiration from:
- Redis INCR-based rate limiting patterns
- Token bucket algorithm implementations
- Production rate limiting experiences

---
