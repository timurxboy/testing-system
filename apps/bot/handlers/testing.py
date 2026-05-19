from html import escape

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from apps.bot.keyboards.inline import (
    CANCEL_TEST_CB,
    OPTION_CB_PREFIX,
    SUBJECT_CB_PREFIX,
    options_keyboard,
    subjects_keyboard,
)
from apps.bot.keyboards.reply import BTN_TAKE_TEST, main_menu
from apps.bot.services.admin_service import AdminService
from apps.bot.services.test_service import TestService
from apps.bot.services.user_service import UserService
from apps.bot.states import Testing

router = Router(name="testing")


def _label_for(index: int) -> str:
    return chr(ord("A") + index)


def _render_question_text(
    *,
    question_text: str,
    options: list[dict],
    position: int,
    total: int,
) -> str:
    lines = [f"<b>Вопрос ({position}/{total})</b>", "", escape(question_text), ""]
    for opt in options:
        lines.append(f"<b>{opt['label']})</b> {escape(opt['text'])}")
    return "\n".join(lines)


# ---- Test session helpers ----------------------------------------------------


async def _send_next_question(
    *,
    chat_message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    data = await state.get_data()
    queue: list[int] = list(data.get("queue", []))
    subject_id: int | None = data.get("subject_id")
    correct: int = int(data.get("correct", 0))
    answered: int = int(data.get("answered", 0))

    if subject_id is None:
        await state.clear()
        await chat_message.answer("Сессия теста не найдена. Нажми «Пройти тесты» снова.")
        return

    test_service = TestService(session)

    while queue:
        question_id = queue.pop(0)
        question = await test_service.get_question_with_options(question_id)
        if question is None or not question.options:
            continue

        options_data: list[dict] = []
        correct_option_id: int | None = None
        for idx, option in enumerate(question.options):
            label = _label_for(idx)
            options_data.append({"id": option.id, "label": label, "text": option.text})
            if option.is_correct and correct_option_id is None:
                correct_option_id = option.id

        await state.update_data(
            queue=queue,
            current_question_id=question.id,
            current_question_text=question.text,
            current_options=options_data,
            correct_option_id=correct_option_id,
        )
        await state.set_state(Testing.answering)

        position = answered + 1
        total = answered + len(queue) + 1

        text = _render_question_text(
            question_text=question.text,
            options=options_data,
            position=position,
            total=total,
        )
        kb = options_keyboard([(o["label"], o["id"]) for o in options_data])
        await chat_message.answer(text, reply_markup=kb)
        return

    await _finish_test(
        chat_message=chat_message,
        state=state,
        session=session,
        correct=correct,
        answered=answered,
    )


async def _finish_test(
    *,
    chat_message: Message,
    state: FSMContext,
    session: AsyncSession,
    correct: int,
    answered: int,
) -> None:
    await state.clear()
    is_admin = await AdminService(session).is_admin(chat_message.chat.id)

    if answered == 0:
        text = "Тест завершён. Вопросы не были отвечены."
    else:
        text = (
            "🎉 <b>Тест завершён!</b>\n"
            f"Правильных ответов: <b>{correct}</b> из <b>{answered}</b>."
        )
    await chat_message.answer(text, reply_markup=main_menu(is_admin=is_admin))


# ---- Entry points ------------------------------------------------------------


@router.message(F.text == BTN_TAKE_TEST)
async def start_test_flow(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    user = await UserService(session).get_by_telegram_id(message.from_user.id)
    if user is None or not user.is_registered:
        await message.answer("Сначала зарегистрируйся — нажми /start.")
        return

    subjects = await TestService(session).list_active_subjects()
    if not subjects:
        await message.answer("Пока нет доступных предметов. Загляни позже.")
        return

    await state.set_state(Testing.choosing_subject)
    await message.answer("Выбери предмет:", reply_markup=subjects_keyboard(subjects))


@router.callback_query(Testing.choosing_subject, F.data.startswith(SUBJECT_CB_PREFIX))
async def choose_subject(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    assert callback.data is not None
    subject_id = int(callback.data.removeprefix(SUBJECT_CB_PREFIX))

    test_service = TestService(session)
    subject = await test_service.get_subject(subject_id)
    if subject is None or not subject.is_active:
        await callback.answer("Предмет недоступен", show_alert=True)
        return

    question_ids = await test_service.list_question_ids_for_subject(subject_id)
    if not question_ids:
        await callback.answer("По этому предмету нет вопросов", show_alert=True)
        return

    user = await UserService(session).get_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.answer("Пользователь не найден, нажми /start", show_alert=True)
        return

    await state.update_data(
        subject_id=subject_id,
        bot_user_id=user.id,
        queue=question_ids,
        correct=0,
        answered=0,
    )

    await callback.message.edit_text(f"Предмет: <b>{escape(subject.name)}</b>")
    await callback.answer()
    await _send_next_question(chat_message=callback.message, state=state, session=session)


@router.callback_query(Testing.answering, F.data.startswith(OPTION_CB_PREFIX))
async def answer_question(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    assert callback.data is not None
    selected_option_id = int(callback.data.removeprefix(OPTION_CB_PREFIX))

    data = await state.get_data()
    current_question_id: int | None = data.get("current_question_id")
    current_question_text: str = data.get("current_question_text", "")
    subject_id: int | None = data.get("subject_id")
    bot_user_id: int | None = data.get("bot_user_id")
    options_data: list[dict] = list(data.get("current_options", []))
    correct_option_id: int | None = data.get("correct_option_id")

    if not current_question_id or not subject_id or not bot_user_id or not options_data:
        await callback.answer("Сессия теста потеряна", show_alert=True)
        await state.clear()
        return

    selected = next((o for o in options_data if o["id"] == selected_option_id), None)
    if selected is None:
        await callback.answer("Неверный вариант", show_alert=True)
        return

    is_correct = selected["id"] == correct_option_id
    correct_opt = next((o for o in options_data if o["id"] == correct_option_id), None)

    await TestService(session).record_attempt(
        bot_user_id=bot_user_id,
        subject_id=subject_id,
        question_id=current_question_id,
        selected_option_id=selected_option_id,
        is_correct=is_correct,
    )

    correct_count = int(data.get("correct", 0)) + (1 if is_correct else 0)
    answered = int(data.get("answered", 0)) + 1
    await state.update_data(
        correct=correct_count,
        answered=answered,
        current_question_id=None,
        current_question_text=None,
        current_options=[],
        correct_option_id=None,
    )

    # Сборка финального текста: исходный вопрос + варианты + вердикт.
    queue_remaining = list(data.get("queue", []))
    position = answered
    total = answered + len(queue_remaining)
    base = _render_question_text(
        question_text=current_question_text,
        options=options_data,
        position=position,
        total=total,
    )

    if is_correct:
        verdict = f"\n\n✅ <b>Правильно!</b>  ({selected['label']})"
    else:
        verdict_lines = [
            "",
            "",
            f"❌ <b>Неверно.</b>",
            f"Ты выбрал: <b>{selected['label']})</b> {escape(selected['text'])}",
        ]
        if correct_opt is not None:
            verdict_lines.append(
                f"Правильный ответ: <b>{correct_opt['label']})</b> {escape(correct_opt['text'])}"
            )
        verdict = "\n".join(verdict_lines)

    await callback.message.edit_text(base + verdict, reply_markup=None)
    await callback.answer()

    await _send_next_question(
        chat_message=callback.message,
        state=state,
        session=session,
    )


@router.callback_query(F.data == CANCEL_TEST_CB)
async def cancel_test(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    data = await state.get_data()
    correct = int(data.get("correct", 0))
    answered = int(data.get("answered", 0))
    await callback.answer("Тест прерван")
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await _finish_test(
        chat_message=callback.message,
        state=state,
        session=session,
        correct=correct,
        answered=answered,
    )
