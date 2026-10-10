import structlog
from dishka.integrations.faststream import FromDishka, inject
from faststream import Context
from faststream.rabbit import RabbitRouter
from tenacity import retry, stop_after_attempt, wait_exponential

from app.infrastructure.rabbitmq.broker import main_queue
from app.services.payment_service import PaymentService

logger = structlog.get_logger()

consumer_router = RabbitRouter()


@consumer_router.subscriber(main_queue)
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
@inject
async def process_payment_message(
    msg: dict,
    payment_service: FromDishka[PaymentService],
    headers: dict = Context("message.headers"),
):
    request_id = headers.get("x-request-id", "unknown")
    payment_id = msg.get("payment_id", "unknown")

    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        payment_id=payment_id,
    )

    logger.info("Received payment message from queue")

    try:
        await payment_service.process_payment(payment_id)
        logger.info("Payment processed successfully")
    except Exception as e:
        logger.exception("Failed to process payment after all retries")
        raise e
