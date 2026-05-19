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

    async def set_first_name(self, user: BotUser, first_name: str) -> BotUser:
        user.first_name = first_name.strip()
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def set_last_name(self, user: BotUser, last_name: str) -> BotUser:
        user.last_name = last_name.strip()
        await self.session.commit()
        await self.session.refresh(user)
        return user
