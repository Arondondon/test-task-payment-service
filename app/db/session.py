import os
import ssl
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings


def build_connect_args() -> dict:
    mode = (settings.db_ssl_mode or "").lower()

    if mode in ("disable", "", "off", "0"):
        return {}

    if mode in ("verify-ca", "verify-full") and not settings.db_ssl_cert:
        raise RuntimeError("DB_SSL_CERT must be provided when using verify-ca or verify-full")

    if settings.db_ssl_cert and os.path.exists(settings.db_ssl_cert):
        ctx = ssl.create_default_context(cafile=settings.db_ssl_cert)
    else:
        ctx = ssl.create_default_context()

    if mode == "verify-full":
        ctx.check_hostname = True
        ctx.verify_mode = ssl.CERT_REQUIRED
    else:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_REQUIRED

    return {"ssl": ctx}


async_engine = create_async_engine(
    url=settings.db_url,
    echo=settings.db_logs,
    connect_args=build_connect_args(),
    pool_pre_ping=True,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
)


async_session_factory = async_sessionmaker(
    async_engine,
    expire_on_commit=False,
)


@asynccontextmanager
async def get_session_context() -> AsyncGenerator[AsyncSession]:
    async with async_session_factory() as session:
        yield session
