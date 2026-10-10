from collections.abc import AsyncIterable

import httpx
from dishka import Provider, Scope, provide
from faststream.rabbit import RabbitBroker
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_factory
from app.infrastructure.api_clients.webhook_sender import WebhookSender
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

    @provide(scope=Scope.APP)
    async def get_httpx_client(self) -> AsyncIterable[httpx.AsyncClient]:
        async with httpx.AsyncClient() as client:
            yield client

    @provide(scope=Scope.REQUEST)
    def get_webhook_sender(self, client: httpx.AsyncClient) -> WebhookSender:
        return WebhookSender(client)

    @provide(scope=Scope.REQUEST)
    async def get_payment_service(
        self, session: AsyncSession, rabbit_broker: RabbitBroker, webhook_sender: WebhookSender
    ) -> PaymentService:
        return PaymentService(session=session, broker=rabbit_broker, webhook_sender=webhook_sender)
