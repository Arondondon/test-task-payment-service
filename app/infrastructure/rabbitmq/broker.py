from faststream.rabbit import RabbitBroker, RabbitExchange, RabbitQueue

from app.core.config import settings
from app.infrastructure.rabbitmq.constants import PAYMENTS_DLQ, PAYMENTS_DLX, PAYMENTS_MAIN_QUEUE

dlx = RabbitExchange(PAYMENTS_DLX)
dlq_queue = RabbitQueue(PAYMENTS_DLQ, routing_key=PAYMENTS_DLQ)

main_queue = RabbitQueue(
    PAYMENTS_MAIN_QUEUE,
    arguments={
        "x-dead-letter-exchange": PAYMENTS_DLX,
        "x-dead-letter-routing-key": PAYMENTS_DLQ,
    },
)

broker = RabbitBroker(settings.amqp_url)
