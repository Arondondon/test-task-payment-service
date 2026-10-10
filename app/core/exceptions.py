import structlog
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

logger = structlog.get_logger()


class BaseAppException(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.detail)


class PaymentNotFoundError(BaseAppException):
    def __init__(self, message: str = "Payment not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=message)


class PaymentAlreadyExistsError(BaseAppException):
    def __init__(self, message: str = "Payment with this Idempotency-Key already processed."):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=message)


class PaymentFailedError(BaseAppException):
    def __init__(self, message: str = "Payment failed."):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)


def register_exception_handlers(app: FastAPI) -> None:
    async def app_exception_handler(request: Request, exc: BaseAppException) -> JSONResponse:
        logger.exception(
            f"HTTP Exception {request.url.path} {exc.status_code}: {exc.detail}", exc_info=exc
        )

        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    async def global_500_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(f"Unhandled internal server error {request.url.path}", exc_info=exc)
        return JSONResponse(status_code=500, content={"detail": "Internal server error."})

    app.add_exception_handler(BaseAppException, app_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, global_500_handler)
