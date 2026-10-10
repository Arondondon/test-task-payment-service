from uuid import uuid4

import pytest
from sqlalchemy import select

from app.core.constants import Currency, PaymentStatus
from app.db.models import Payment
from app.services.payment_service import PaymentService


class TestOutboxWorkerAndConsumer:
    @pytest.mark.asyncio
    async def test_payment_consumer_success(self, dishka_container, test_session_maker):
        payment_id = uuid4()

        async with test_session_maker() as session:
            payment = Payment(
                id=payment_id,
                amount=150.00,
                currency=Currency.USD,
                description="Consumer test payment",
                status=PaymentStatus.pending,
                idempotency_key=str(uuid4()),
            )
            session.add(payment)
            await session.commit()

        async with dishka_container() as req_container:
            payment_service = await req_container.get(PaymentService)
            await payment_service.process_payment(payment_id)

        async with test_session_maker() as session:
            updated_payment = (
                await session.execute(select(Payment).where(Payment.id == payment_id))
            ).scalar_one()

            assert updated_payment.status == PaymentStatus.succeeded
