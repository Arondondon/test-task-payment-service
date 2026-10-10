import asyncio
import random
from uuid import UUID, uuid4

import structlog
from faststream.rabbit import RabbitBroker
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.payment_schemas import (
    CreatePaymentRequest,
    CreatePaymentResponse,
    GetPaymentResponse,
)
from app.core.constants import OutboxEventStatus, PaymentStatus
from app.core.exceptions import PaymentAlreadyExistsError, PaymentFailedError, PaymentNotFoundError
from app.db.models import OutboxEvent, Payment
from app.infrastructure.api_clients.webhook_sender import WebhookSender
from app.infrastructure.rabbitmq.constants import PAYMENTS_MAIN_QUEUE
from app.infrastructure.rabbitmq.schemas import PaymentEvent
from app.repositories.outbox_event_repository import OutboxEventRepository
from app.repositories.payment_repository import PaymentRepository

logger = structlog.get_logger()


class PaymentService:
    def __init__(self, session: AsyncSession, broker: RabbitBroker, webhook_sender: WebhookSender):
        self._session = session
        self._broker = broker
        self._webhook_sender = webhook_sender
        self._payment_repo = PaymentRepository(session=session)
        self._outbox_repo = OutboxEventRepository(session=session)

    async def create_payment(
        self, request: CreatePaymentRequest, idempotency_key: str
    ) -> CreatePaymentResponse:
        existing_payment = await self._payment_repo.get_by_idempotency_key(idempotency_key)
        if existing_payment:
            return self._verify_and_return_existing(existing_payment, request)

        payment_id = uuid4()
        payment = Payment(
            id=payment_id,
            amount=request.amount,
            currency=request.currency,
            description=request.description,
            metadata_info=request.metadata_info,
            webhook_url=request.webhook_url,
            status=PaymentStatus.pending,
            idempotency_key=idempotency_key,
        )

        ctx = structlog.contextvars.get_contextvars()
        request_id = ctx.get("request_id", "unknown")

        event_payload = PaymentEvent(payment_id=payment_id)

        outbox_event = OutboxEvent(
            id=uuid4(),
            payload=event_payload.model_dump(mode="json"),
            headers={"x-request-id": request_id},
            status=OutboxEventStatus.pending,
        )

        try:
            async with self._session.begin_nested():
                self._payment_repo.add(payment)
                self._outbox_repo.add(outbox_event)
                await self._session.flush()

        except IntegrityError:
            existing_payment = await self._payment_repo.get_by_idempotency_key(idempotency_key)
            if existing_payment:
                return self._verify_and_return_existing(existing_payment, request)
            raise

        await self._session.commit()

        logger.info("Payment and outbox event created", payment_id=str(payment_id))

        return CreatePaymentResponse(
            payment_id=payment.id, status=payment.status, created_at=payment.created_at
        )

    async def get_payment(self, payment_id: UUID) -> GetPaymentResponse:
        payment = await self._payment_repo.get_by_id(payment_id)
        if not payment:
            raise PaymentNotFoundError()

        return GetPaymentResponse(
            payment_id=payment.id,
            amount=payment.amount,
            currency=payment.currency,
            description=payment.description,
            metadata_info=payment.metadata_info,
            created_at=payment.created_at,
            updated_at=payment.updated_at,
        )

    async def process_pending_events(self) -> None:
        async with self._session.begin():
            events = await self._outbox_repo.get_pending_events()
            if not events:
                return

            for event in events:
                await self._broker.publish(
                    message=event.payload, queue=PAYMENTS_MAIN_QUEUE, headers=event.headers
                )
                event.status = OutboxEventStatus.published

        logger.info(f"Published {len(events)} outbox events to broker")

    async def process_payment(self, payment_id: UUID) -> None:
        async with self._session.begin():
            payment = await self._payment_repo.get_by_id(payment_id)
            if not payment:
                logger.error(f"Payment not found during processing (payment_id={payment_id})")
                return

            await self._simulate_processing()

            payment.status = PaymentStatus.succeeded

            webhook_url = payment.webhook_url
            status_to_send = payment.status.value

            logger.info(f"Payment {payment_id} marked as COMPLETED")

        if webhook_url:
            try:
                await self._webhook_sender.send_payment_status(
                    url=webhook_url, payment_id=str(payment_id), status=status_to_send
                )
            except Exception:
                logger.exception(
                    f"Failed to send webhook after all retries. Payment {payment_id} remains COMPLETED."
                )

    def _verify_and_return_existing(
        self, payment: Payment, request: CreatePaymentRequest
    ) -> CreatePaymentResponse:
        if payment.amount != request.amount or payment.currency != request.currency:
            logger.warning(
                "Idempotency key collision with different parameters",
                idempotency_key=payment.idempotency_key,
            )
            raise PaymentAlreadyExistsError(
                "A payment with this Idempotency-Key exists but has different parameters."
            )

        logger.info("Returning existing payment for idempotency key", payment_id=str(payment.id))
        return CreatePaymentResponse(
            payment_id=payment.id, status=payment.status, created_at=payment.created_at
        )

    async def _simulate_processing(self) -> None:
        logger.info("Starting payment processing emulation")

        await asyncio.sleep(random.uniform(2.0, 5.0))

        if random.random() < 0.1:
            logger.exception("Simulated payment failed")
            raise PaymentFailedError("Simulated payment failed.")

        logger.info("Successfully completed payment processing emulation")
