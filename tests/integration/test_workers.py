from uuid import uuid4

import pytest
from sqlalchemy import select

from app.core.constants import OutboxEventStatus
from app.db.models import OutboxEvent
from app.infrastructure.rabbitmq.constants import PAYMENTS_MAIN_QUEUE
from app.infrastructure.rabbitmq.schemas import PaymentEvent
from app.services.payment_service import PaymentService


class TestOutboxWorkerAndConsumer:
    @pytest.mark.asyncio
    async def test_outbox_worker_success(self, dishka_container, test_session_maker, test_broker):
        payment_id = uuid4()
        event_payload = PaymentEvent(payment_id=payment_id)

        async with test_session_maker() as session:
            outbox_event = OutboxEvent(
                id=uuid4(),
                queue_name=PAYMENTS_MAIN_QUEUE,
                payload=event_payload.model_dump(mode="json"),
                headers={"x-request-id": "test-worker-req"},
                status=OutboxEventStatus.pending,
            )
            session.add(outbox_event)
            await session.commit()
            outbox_id = outbox_event.id

        async with dishka_container() as req_container:
            payment_service = await req_container.get(PaymentService)
            await payment_service.process_pending_events()

        async with test_session_maker() as session:
            updated_event = (
                await session.execute(select(OutboxEvent).where(OutboxEvent.id == outbox_id))
            ).scalar_one()

            assert updated_event.status == OutboxEventStatus.published
