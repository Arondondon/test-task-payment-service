import abc
import asyncio
from contextlib import suppress

import structlog
from dishka import AsyncContainer

logger = structlog.get_logger()


class BaseWorker(abc.ABC):
    def __init__(
        self,
        default_interval_seconds: int,
        interval_seconds: int | None = None,
        container: AsyncContainer | None = None,
    ):
        self._interval_seconds = (
            default_interval_seconds if interval_seconds is None else interval_seconds
        )
        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()
        self._container = container
        self.worker_name = self.__class__.__name__

    def start(self) -> None:
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"{self.worker_name} started. Interval: {self._interval_seconds}s")

    async def stop(self) -> None:
        self._stop_event.set()
        if self._task:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
        logger.info(f"{self.worker_name} stopped")

    async def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                await self.process_iteration()
            except Exception:
                logger.exception(f"Error in {self.worker_name}")

            with suppress(TimeoutError):
                await asyncio.wait_for(self._stop_event.wait(), timeout=self._interval_seconds)

    @abc.abstractmethod
    async def process_iteration(self):
        pass
