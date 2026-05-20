from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from apps.bot import text
from apps.bot.keyboards.reply import main_menu
from apps.bot.services.admin_service import AdminService
from apps.bot.services.user_service import UserService

router = Router(name="menu")


@router.message(Command("menu"))
@router.message(F.text == "/menu")
async def cmd_menu(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await state.clear()
    user = await UserService(session).get_by_telegram_id(message.from_user.id)
    if user is None or not user.is_registered:
        await message.answer(text.NOT_REGISTERED)
        return

    is_admin = await AdminService(session).is_admin(message.from_user.id)
    await message.answer(text.MENU_PROMPT, reply_markup=main_menu(is_admin=is_admin))
