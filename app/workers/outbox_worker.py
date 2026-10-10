import asyncio

from dishka import AsyncContainer

from app.core.config import settings
from app.services.payment_service import PaymentService
from app.workers.base_worker import BaseWorker


class OutboxWorker(BaseWorker):
    def __init__(self, container: AsyncContainer, interval_seconds: int | None = None):
        super().__init__(
            default_interval_seconds=settings.outbox_worker_interval_seconds,
            interval_seconds=interval_seconds,
            container=container,
        )

    async def process_iteration(self):
        async with self._container() as request_container:
            payment_service = await request_container.get(PaymentService)
            processed_count = await payment_service.process_pending_events()

        if processed_count == 0:
            await asyncio.sleep(self._interval_seconds)
