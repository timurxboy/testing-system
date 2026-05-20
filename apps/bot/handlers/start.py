from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from apps.bot import text
from apps.bot.keyboards.inline import QCOUNT_CB_PREFIX, question_count_keyboard
from apps.bot.keyboards.reply import main_menu, remove_keyboard
from apps.bot.models.bot_user import QUESTION_COUNT_CHOICES
from apps.bot.services.admin_service import AdminService
from apps.bot.services.user_service import UserService
from apps.bot.states import Registration, Settings

router = Router(name="start")

_MIN_ID_LEN = 1
_MAX_ID_LEN = 64


def _is_valid_student_id(raw: str) -> bool:
    s = raw.strip()
    return _MIN_ID_LEN <= len(s) <= _MAX_ID_LEN


async def _show_main_menu(message: Message, session: AsyncSession, user) -> None:
    is_admin = await AdminService(session).is_admin(user.telegram_id)
    await message.answer(
        text.WELCOME_BACK.format(student_id=user.student_id),
        reply_markup=main_menu(
            is_admin=is_admin, question_count=user.preferred_question_count
        ),
    )


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await state.clear()

    user_service = UserService(session)
    user = await user_service.get_or_create(
        telegram_id=message.from_user.id,
        telegram_username=message.from_user.username,
    )

    if not user.is_registered:
        await state.set_state(Registration.waiting_for_student_id)
        await message.answer(text.WELCOME_NEW, reply_markup=remove_keyboard())
        return

    if user.preferred_question_count is None:
        await state.set_state(Registration.waiting_for_question_count)
        await message.answer(
            text.CHOOSE_QUESTION_COUNT,
            reply_markup=question_count_keyboard(QUESTION_COUNT_CHOICES),
        )
        return

    await _show_main_menu(message, session, user)


@router.message(Registration.waiting_for_student_id, F.text)
async def receive_student_id(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    raw = message.text or ""
    if not _is_valid_student_id(raw):
        await message.answer(text.INVALID_STUDENT_ID)
        return

    student_id = raw.strip()
    user_service = UserService(session)

    user = await user_service.get_by_telegram_id(message.from_user.id)
    if user is None:
        await state.clear()
        await message.answer(text.SESSION_LOST)
        return

    existing = await user_service.get_by_student_id(student_id)
    if existing is not None and existing.id != user.id:
        await message.answer(text.STUDENT_ID_TAKEN)
        return

    user = await user_service.set_student_id(user, student_id)

    await state.set_state(Registration.waiting_for_question_count)
    await message.answer(text.REGISTRATION_OK, reply_markup=remove_keyboard())
    await message.answer(
        text.CHOOSE_QUESTION_COUNT,
        reply_markup=question_count_keyboard(QUESTION_COUNT_CHOICES),
    )


@router.callback_query(
    Registration.waiting_for_question_count, F.data.startswith(QCOUNT_CB_PREFIX)
)
@router.callback_query(
    Settings.choosing_question_count, F.data.startswith(QCOUNT_CB_PREFIX)
)
async def choose_question_count(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    assert callback.data is not None
    try:
        count = int(callback.data.removeprefix(QCOUNT_CB_PREFIX))
    except ValueError:
        await callback.answer()
        return
    if count not in QUESTION_COUNT_CHOICES:
        await callback.answer()
        return

    user_service = UserService(session)
    user = await user_service.get_by_telegram_id(callback.from_user.id)
    if user is None:
        await state.clear()
        await callback.answer(text.SESSION_LOST, show_alert=True)
        return

    user = await user_service.set_question_count(user, count)
    await state.clear()

    is_admin = await AdminService(session).is_admin(callback.from_user.id)
    await callback.answer()
    try:
        await callback.message.edit_text(
            text.QUESTION_COUNT_SAVED.format(count=count)
        )
    except Exception:
        pass
    await callback.message.answer(
        text.MENU_PROMPT,
        reply_markup=main_menu(
            is_admin=is_admin, question_count=user.preferred_question_count
        ),
    )
