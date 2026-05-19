from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from apps.bot.keyboards.reply import main_menu, remove_keyboard
from apps.bot.services.admin_service import AdminService
from apps.bot.services.user_service import UserService
from apps.bot.states import Registration

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await state.clear()

    user_service = UserService(session)
    user = await user_service.get_or_create(
        telegram_id=message.from_user.id,
        telegram_username=message.from_user.username,
    )

    if not user.is_registered:
        await state.set_state(Registration.waiting_for_first_name)
        await message.answer(
            "Привет! Давай познакомимся.\nКак тебя зовут? Напиши <b>имя</b>.",
            reply_markup=remove_keyboard(),
        )
        return

    is_admin = await AdminService(session).is_admin(message.from_user.id)
    await message.answer(
        f"С возвращением, {user.first_name}!\nВыбери действие в меню ниже.",
        reply_markup=main_menu(is_admin=is_admin),
    )


@router.message(Registration.waiting_for_first_name, F.text)
async def receive_first_name(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    first_name = (message.text or "").strip()
    if not first_name or len(first_name) > 120:
        await message.answer("Введи корректное имя (до 120 символов).")
        return

    user = await UserService(session).get_by_telegram_id(message.from_user.id)
    if user is None:
        await state.clear()
        await message.answer("Что-то пошло не так. Нажми /start ещё раз.")
        return

    await UserService(session).set_first_name(user, first_name)
    await state.set_state(Registration.waiting_for_last_name)
    await message.answer("Отлично! Теперь напиши <b>фамилию</b>.")


@router.message(Registration.waiting_for_last_name, F.text)
async def receive_last_name(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    last_name = (message.text or "").strip()
    if not last_name or len(last_name) > 120:
        await message.answer("Введи корректную фамилию (до 120 символов).")
        return

    user = await UserService(session).get_by_telegram_id(message.from_user.id)
    if user is None:
        await state.clear()
        await message.answer("Что-то пошло не так. Нажми /start ещё раз.")
        return

    await UserService(session).set_last_name(user, last_name)
    await state.clear()

    is_admin = await AdminService(session).is_admin(message.from_user.id)
    await message.answer(
        f"Готово, {user.first_name} {last_name}! Можешь приступать к тестам.",
        reply_markup=main_menu(is_admin=is_admin),
    )
