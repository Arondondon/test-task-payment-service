from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.constants import Currency, PaymentStatus
from app.db.models import OutboxEvent, Payment


class TestCreatePaymentEndpoint:
    @pytest.mark.asyncio
    async def test_create_payment_success(self, client: AsyncClient, test_session_maker):
        idempotency_key = str(uuid4())
        payload = {
            "amount": "100.50",
            "currency": "USD",
            "description": "Test order payment",
            "metadata_info": {"order_id": 123},
            "webhook_url": "https://example.com/webhook",
        }
        headers = {"Idempotency-Key": idempotency_key, "X-Request-ID": "test-req-123"}

        response = await client.post("/api/v1/payments", json=payload, headers=headers)

        assert response.status_code == 202
        data = response.json()
        assert "payment_id" in data
        assert data["status"] == PaymentStatus.pending.value
        assert "created_at" in data

        # Проверяем записи в БД (Payment и OutboxEvent)
        async with test_session_maker() as session:
            payment = (
                await session.execute(
                    select(Payment).where(Payment.idempotency_key == idempotency_key)
                )
            ).scalar_one_or_none()
            assert payment is not None
            assert payment.amount == Decimal("100.50")
            assert payment.currency == Currency.USD

            outbox_events = (await session.execute(select(OutboxEvent))).scalars().all()
            outbox = next(
                (e for e in outbox_events if e.payload.get("payment_id") == str(payment.id)), None
            )
            assert outbox is not None
            assert outbox.headers.get("x-request-id") == "test-req-123"

    @pytest.mark.asyncio
    async def test_create_payment_idempotent_retry_returns_same_result(self, client: AsyncClient):
        idempotency_key = str(uuid4())
        payload = {
            "amount": "250.00",
            "currency": "EUR",
            "description": "First attempt",
        }
        headers = {"Idempotency-Key": idempotency_key}

        # Первичный запрос
        res1 = await client.post("/api/v1/payments", json=payload, headers=headers)
        assert res1.status_code == 202
        data1 = res1.json()

        # Повторный запрос с ТЕМ ЖЕ Idempotency-Key и идентичным body
        res2 = await client.post("/api/v1/payments", json=payload, headers=headers)
        assert res2.status_code == 202
        data2 = res2.json()

        assert data1["payment_id"] == data2["payment_id"]
        assert data1["status"] == data2["status"]

    @pytest.mark.asyncio
    async def test_create_payment_idempotency_key_collision_different_body_returns_409(
        self, client: AsyncClient
    ):
        idempotency_key = str(uuid4())
        payload1 = {"amount": "100.00", "currency": "USD"}
        payload2 = {"amount": "999.00", "currency": "USD"}  # Изменен сумма
        headers = {"Idempotency-Key": idempotency_key}

        res1 = await client.post("/api/v1/payments", json=payload1, headers=headers)
        assert res1.status_code == 202

        # Повторный запрос с тем же ключом, но другими параметрами
        res2 = await client.post("/api/v1/payments", json=payload2, headers=headers)
        assert res2.status_code == 409
        assert "different parameters" in res2.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_payment_missing_idempotency_key_header_returns_422(
        self, client: AsyncClient
    ):
        payload = {"amount": "100.00", "currency": "USD"}
        # Не передаем Header Idempotency-Key
        response = await client.post("/api/v1/payments", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_payment_invalid_body_returns_422(self, client: AsyncClient):
        idempotency_key = str(uuid4())
        headers = {"Idempotency-Key": idempotency_key}

        # Отрицательная сумма
        payload = {"amount": "-50.00", "currency": "USD"}
        response = await client.post("/api/v1/payments", json=payload, headers=headers)
        assert response.status_code == 422


class TestGetPaymentEndpoint:
    @pytest.mark.asyncio
    async def test_get_payment_success(self, client: AsyncClient):
        # Сначала создаем платеж
        idempotency_key = str(uuid4())
        payload = {
            "amount": "500.00",
            "currency": "EUR",
            "description": "Details test",
            "metadata_info": {"customer_id": "cust_1"},
        }
        create_res = await client.post(
            "/api/v1/payments", json=payload, headers={"Idempotency-Key": idempotency_key}
        )
        payment_id = create_res.json()["payment_id"]

        # Запрашиваем созданный платеж
        response = await client.get(f"/api/v1/payments/{payment_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["payment_id"] == payment_id
        assert data["amount"] == "500.00"
        assert data["currency"] == "EUR"
        assert data["description"] == "Details test"
        assert data["metadata_info"] == {"customer_id": "cust_1"}
        assert data["status"] == PaymentStatus.pending.value
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_get_payment_not_found_returns_404(self, client: AsyncClient):
        non_existent_id = uuid4()
        response = await client.get(f"/api/v1/payments/{non_existent_id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Payment not found"

    @pytest.mark.asyncio
    async def test_get_payment_invalid_uuid_returns_422(self, client: AsyncClient):
        response = await client.get("/api/v1/payments/not-a-valid-uuid")
        assert response.status_code == 422
