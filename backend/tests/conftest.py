import os
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import NullPool

from app.api.main import app
from app.api.deps.auth import require_user
from app.core import config as cfg
from app.core.database import get_db
from app.core.redis_client import set_test_client
from app.models.base import Base
from app.services.auth.base import Principal

# Disable Redis by default — caching / rate-limit / idempotency become no-ops
# unless a test installs a fakeredis client via the `fake_redis` fixture.
cfg.settings.redis_disabled = True
# MinIO simulator-mode by default so tests don't need a running MinIO.
cfg.settings.minio_disabled = True

TEST_DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5437/dclaw_crisis_test",
)

test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)


async def override_get_db():
    async with AsyncSession(test_engine, expire_on_commit=False) as session:
        try:
            yield session
        finally:
            await session.close()


def _override_require_user():
    """Default override for tests: every protected endpoint sees a synthetic user.

    Tests that exercise auth behavior itself (test_auth.py) clear or replace
    this override locally so they hit the real dependency.
    """
    return Principal(user_id="test-user", email="[email protected]", is_admin=True)


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[require_user] = _override_require_user


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def unauthenticated_client():
    """Client without the require_user override — real auth is enforced."""
    app.dependency_overrides.pop(require_user, None)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac
    finally:
        app.dependency_overrides[require_user] = _override_require_user


@pytest_asyncio.fixture
async def fake_redis():
    """Inject a fakeredis async client for tests exercising cache/ratelimit/idempotency."""
    import fakeredis.aioredis as fa
    client = fa.FakeRedis(decode_responses=True)
    set_test_client(client)
    cfg.settings.redis_disabled = False
    try:
        yield client
    finally:
        await client.aclose()
        set_test_client(None)
        cfg.settings.redis_disabled = True
