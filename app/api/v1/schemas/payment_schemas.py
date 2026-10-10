from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.constants import Currency, PaymentStatus


class CreatePaymentRequest(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    currency: Currency
    description: str | None = Field(default=None)
    metadata_info: dict[str, Any] | None = Field(default=None)
    webhook_url: str | None = Field(default=None)


class CreatePaymentResponse(BaseModel):
    payment_id: UUID
    status: PaymentStatus
    created_at: datetime


class GetPaymentResponse(BaseModel):
    payment_id: UUID
    amount: Decimal
    currency: Currency
    description: str | None
    metadata_info: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime
