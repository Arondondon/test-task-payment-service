from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.infrastructure.rabbitmq.broker import broker
from app.workers.outbox_worker import OutboxWorker


@asynccontextmanager
async def lifespan(app: FastAPI):
    container = app.state.dishka_container

    await broker.connect()

    worker = OutboxWorker(container=container)
    await worker.start()

    try:
        yield
    finally:
        await worker.stop()
        await broker.disconnect()
