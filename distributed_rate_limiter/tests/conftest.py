import pytest
import redis
import asyncio


REDIS_URL = "redis://localhost:6379/15"


@pytest.fixture(scope="session", autouse=True)
def flush_redis():
    """
    Ensure a clean Redis DB before and after test session.
    """
    client = redis.Redis.from_url(REDIS_URL)
    client.flushdb()
    yield
    client.flushdb()


@pytest.fixture
def redis_url():
    return REDIS_URL


@pytest.fixture
def event_loop():
    """
    pytest-asyncio compatibility.
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
