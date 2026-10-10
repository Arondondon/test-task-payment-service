from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import JSON, Enum, Numeric, String
from sqlalchemy import UUID as SA_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import Currency, OutboxEventStatus, PaymentStatus
from app.db.base import Base


class Payment(Base):
    __tablename__ = "payment"

    id: Mapped[UUID] = mapped_column(SA_UUID(as_uuid=True), primary_key=True, default=uuid4)
    amount: Mapped[Decimal] = mapped_column("amount", Numeric(14, 2), nullable=False)
    currency: Mapped[Currency] = mapped_column(
        Enum(Currency, native_enum=False, length=3), nullable=False
    )
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    metadata_info: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, native_enum=False), nullable=False
    )
    idempotency_key: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    webhook_url: Mapped[str | None] = mapped_column(String, nullable=True)


class OutboxEvent(Base):
    id: Mapped[UUID] = mapped_column(SA_UUID(as_uuid=True), primary_key=True, default=uuid4)
    queue_name: Mapped[str] = mapped_column(String, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    headers: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[OutboxEventStatus] = mapped_column(
        Enum(OutboxEventStatus, native_enum=False), nullable=False
    )
