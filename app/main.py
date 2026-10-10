from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka as setup_dishka_fastapi
from dishka.integrations.faststream import setup_dishka as setup_dishka_faststream
from fastapi import FastAPI

from app.api import router
from app.consumers.payment_consumer import consumer_router
from app.core.config import settings
from app.core.dependencies import MainProvider
from app.core.lifespan import lifespan
from app.core.logger import setup_logger
from app.core.middleware import logging_middleware
from app.infrastructure.rabbitmq.broker import broker

setup_logger(is_production=settings.stage == "prod")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Payment Processing Service",
        description="Microservice for handling payments with Outbox pattern",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.include_router(router, prefix="/api/v1")

    app.middleware("http")(logging_middleware)

    return app


app = create_app()

broker.include_router(consumer_router)

container = make_async_container(MainProvider())
setup_dishka_fastapi(container, app)
setup_dishka_faststream(container, broker)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="localhost", port=settings.port)
