import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_fixed

logger = structlog.get_logger()


class WebhookSender:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1), reraise=True)
    async def send_payment_status(self, url: str, payment_id: str, status: str) -> None:
        payload = {"payment_id": payment_id, "status": status}

        logger.info("Attempting to send webhook", webhook_url=url)

        try:
            response = await self.client.post(url, json=payload, timeout=5.0)
            response.raise_for_status()
            logger.info(f"Webhook sent successfully, status={response.status_code}")

        except httpx.HTTPError as e:
            logger.exception("Webhook HTTP error")
            raise e
