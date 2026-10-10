from collections.abc import AsyncIterable

from dishka import Provider, Scope, provide
from faststream.rabbit import RabbitBroker
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_factory
from app.infrastructure.rabbitmq.broker import broker
from app.services.payment_service import PaymentService


class MainProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def get_session(self) -> AsyncIterable[AsyncSession]:
        async with async_session_factory() as session:
            yield session

    @provide(scope=Scope.APP)
    async def get_broker(self) -> RabbitBroker:
        return broker

    @provide(scope=Scope.REQUEST)
    async def get_payment_service(self, session: AsyncSession) -> PaymentService:
        return PaymentService(session=session)
