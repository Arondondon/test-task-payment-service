import uuid

import structlog
from fastapi import Request

logger = structlog.get_logger()


async def logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        path=request.url.path,
        method=request.method,
    )

    logger.info("Received request")
    response = await call_next(request)
    logger.info("Processed request", status_code=response.status_code)

    return response
