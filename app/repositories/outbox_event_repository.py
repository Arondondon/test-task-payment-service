from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import OutboxEventStatus
from app.db.models import OutboxEvent


class OutboxEventRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    def add(self, event: OutboxEvent) -> None:
        self.session.add(event)

    async def get_pending_events(self, limit: int = 100) -> list[OutboxEvent]:
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.status == OutboxEventStatus.pending)
            .order_by(OutboxEvent.created_at.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
