import os
from collections.abc import AsyncGenerator

import pytest_asyncio
from dishka import AsyncContainer, Provider, Scope, make_async_container, provide
from faststream.rabbit import RabbitBroker
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer
from testcontainers.rabbitmq import RabbitMqContainer

from app.core.auth import verify_api_key

os.environ["TESTCONTAINERS_RYUK_DISABLED"] = "true"

from app.core.dependencies import MainProvider
from app.db.base import Base
from app.db.models import OutboxEvent, Payment  # noqa: F401
from app.main import app as fastapi_app


@pytest_asyncio.fixture(scope="session")
def postgres_container():
    container = PostgresContainer("postgres:16-alpine", driver="asyncpg")
    container.start()
    yield container
    container.stop()


@pytest_asyncio.fixture(scope="session")
def rabbitmq_container():
    container = RabbitMqContainer("rabbitmq:3.13-management-alpine")
    container.start()
    yield container
    container.stop()


@pytest_asyncio.fixture(scope="function")
async def test_engine(postgres_container):
    engine = create_async_engine(postgres_container.get_connection_url(), echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_session_maker(test_engine):
    return async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture(scope="function")
async def test_broker(rabbitmq_container):
    host = rabbitmq_container.get_container_host_ip()
    port = rabbitmq_container.get_exposed_port(5672)
    user = rabbitmq_container.username
    password = rabbitmq_container.password

    amqp_url = f"amqp://{user}:{password}@{host}:{port}/"
    broker = RabbitBroker(amqp_url)
    await broker.connect()

    yield broker

    await broker.close()


class TestProvider(Provider):
    def __init__(self, session_maker: async_sessionmaker[AsyncSession], broker: RabbitBroker):
        super().__init__()
        self._session_maker = session_maker
        self._broker = broker

    @provide(scope=Scope.REQUEST)
    async def get_session(self) -> AsyncGenerator[AsyncSession]:
        async with self._session_maker() as session:
            yield session

    @provide(scope=Scope.APP)
    async def get_broker(self) -> RabbitBroker:
        return self._broker


@pytest_asyncio.fixture(scope="function")
async def dishka_container(test_session_maker, test_broker) -> AsyncGenerator[AsyncContainer]:
    test_provider = TestProvider(session_maker=test_session_maker, broker=test_broker)
    container = make_async_container(MainProvider(), test_provider)

    fastapi_app.state.dishka_container = container

    yield container

    await container.close()


@pytest_asyncio.fixture(scope="function")
async def client(dishka_container) -> AsyncGenerator[AsyncClient]:
    fastapi_app.dependency_overrides[verify_api_key] = lambda: None

    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app),
        base_url="http://testserver",
    ) as ac:
        yield ac
