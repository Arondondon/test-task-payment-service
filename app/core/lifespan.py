from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from faststream.rabbit import RabbitBroker

from app.workers.outbox_worker import OutboxWorker


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    container = app.state.dishka_container

    broker = await container.get(RabbitBroker)
    await broker.start()

    worker = OutboxWorker(container=container)
    worker.start()

    try:
        yield
    finally:
        await worker.stop()
        await broker.disconnect()
