from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, Header, status

from app.api.v1.schemas.payment_schemas import (
    CreatePaymentRequest,
    CreatePaymentResponse,
    GetPaymentResponse,
)
from app.core.auth import verify_api_key
from app.services.payment_service import PaymentService

payment_router = APIRouter(
    prefix="/payments", tags=["payments"], dependencies=[Depends(verify_api_key)]
)


@payment_router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=CreatePaymentResponse)
@inject
async def create_payment(
    request: CreatePaymentRequest,
    payment_service: FromDishka[PaymentService],
    idempotency_key: str = Header(alias="Idempotency-Key"),
) -> CreatePaymentResponse:
    return await payment_service.create_payment(request, idempotency_key)


@payment_router.get(
    "/{payment_id}", status_code=status.HTTP_200_OK, response_model=GetPaymentResponse
)
@inject
async def get_payment(
    payment_id: UUID,
    payment_service: FromDishka[PaymentService],
) -> GetPaymentResponse:
    return await payment_service.get_payment(payment_id)
