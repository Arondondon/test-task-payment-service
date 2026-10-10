from faststream.rabbit import RabbitBroker, RabbitExchange, RabbitQueue

from app.core.config import settings

dlx = RabbitExchange("dlq_exchange")
dlq_queue = RabbitQueue("dlq_payments", routing_key="dlq_routing")

main_queue = RabbitQueue(
    "payments.new",
    arguments={
        "x-dead-letter-exchange": "dlq_exchange",
        "x-dead-letter-routing-key": "dlq_routing",
    },
)

broker = RabbitBroker(settings.amqp_url)
