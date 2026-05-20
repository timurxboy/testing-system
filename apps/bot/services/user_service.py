from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.bot.models.bot_user import BotUser


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> BotUser | None:
        result = await self.session.execute(
            select(BotUser).where(BotUser.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_by_student_id(self, student_id: str) -> BotUser | None:
        result = await self.session.execute(
            select(BotUser).where(BotUser.student_id == student_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        *,
        telegram_id: int,
        telegram_username: str | None,
    ) -> BotUser:
        user = await self.get_by_telegram_id(telegram_id)
        if user is None:
            user = BotUser(
                telegram_id=telegram_id,
                telegram_username=telegram_username,
            )
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
            return user

        if telegram_username and user.telegram_username != telegram_username:
            user.telegram_username = telegram_username
            await self.session.commit()
            await self.session.refresh(user)

        return user

    async def set_student_id(self, user: BotUser, student_id: str) -> BotUser:
        user.student_id = student_id.strip()
        await self.session.commit()
        await self.session.refresh(user)
        return user
