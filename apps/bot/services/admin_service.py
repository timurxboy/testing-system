from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.bot.models.tg_admin import TgAdmin


class AdminService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def is_admin(self, telegram_id: int) -> bool:
        result = await self.session.execute(
            select(TgAdmin.id).where(
                TgAdmin.telegram_id == telegram_id,
                TgAdmin.is_active.is_(True),
            )
        )
        return result.first() is not None
