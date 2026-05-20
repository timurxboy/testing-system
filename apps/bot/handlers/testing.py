from html import escape

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from apps.bot import text
from apps.bot.keyboards.inline import (
    CANCEL_TEST_CB,
    OPTION_CB_PREFIX,
    SUBJECT_CB_PREFIX,
    options_keyboard,
    subjects_keyboard,
)
from apps.bot.keyboards.reply import main_menu
from apps.bot.models.attempt_session import AttemptSession
from apps.bot.services.admin_service import AdminService
from apps.bot.services.attempt_service import AttemptService, AttemptStartError
from apps.bot.services.test_service import TestService
from apps.bot.services.user_service import UserService
from apps.bot.states import Testing

router = Router(name="testing")


def _grade_for(percent: float) -> str:
    if percent >= 90:
        return text.GRADE_EXCELLENT
    if percent >= 80:
        return text.GRADE_GOOD
    if percent >= 70:
        return text.GRADE_SATISFACTORY
    return text.GRADE_UNSATISFACTORY


def _result_body(
    *, correct: int, total: int, cancelled: bool
) -> str:
    if total == 0:
        return text.TEST_NO_ANSWERS
    percent = correct / total * 100
    header = text.TEST_CANCELLED_HEADER if cancelled else text.TEST_FINISHED_HEADER
    line = text.TEST_FINISHED_LINE.format(correct=correct, total=total, percent=percent)
    grade = text.TEST_FINISHED_GRADE.format(grade=_grade_for(percent))
    return f"{header}\n{line}\n{grade}"


def _label_for(index: int) -> str:
    return chr(ord("A") + index)


def _render_question_text(
    *,
    question_text: str,
    options: list[dict],
    position: int,
    total: int,
) -> str:
    lines = [
        text.QUESTION_HEADER.format(position=position, total=total),
        "",
        escape(question_text),
        "",
    ]
    for opt in options:
        lines.append(text.OPTION_LINE.format(label=opt["label"], text=escape(opt["text"])))
    return "\n".join(lines)


# ---- Session helpers ---------------------------------------------------------


async def _show_current_question(
    *,
    chat_message: Message,
    state: FSMContext,
    session: AsyncSession,
    attempt_session: AttemptSession,
) -> None:
    attempt_service = AttemptService(session)
    next_qid = attempt_service.next_question_id(attempt_session)

    if next_qid is None:
        await _finish_attempt(
            chat_message=chat_message,
            state=state,
            session=session,
            attempt_session=attempt_session,
        )
        return

    question = await TestService(session).get_question_with_options(next_qid)
    # На случай, если вопрос/варианты удалили — пропускаем его.
    while question is None or not question.options:
        attempt_session = await attempt_service.advance(attempt_session, is_correct=False)
        next_qid = attempt_service.next_question_id(attempt_session)
        if next_qid is None:
            await _finish_attempt(
                chat_message=chat_message,
                state=state,
                session=session,
                attempt_session=attempt_session,
            )
            return
        question = await TestService(session).get_question_with_options(next_qid)

    options_data: list[dict] = []
    correct_option_id: int | None = None
    for idx, option in enumerate(question.options):
        label = _label_for(idx)
        options_data.append({"id": option.id, "label": label, "text": option.text})
        if option.is_correct and correct_option_id is None:
            correct_option_id = option.id

    await state.update_data(
        attempt_session_id=attempt_session.id,
        current_question_id=question.id,
        current_question_text=question.text,
        current_options=options_data,
        correct_option_id=correct_option_id,
    )
    await state.set_state(Testing.answering)

    position = attempt_session.current_index + 1
    total = attempt_session.total_questions
    body = _render_question_text(
        question_text=question.text,
        options=options_data,
        position=position,
        total=total,
    )
    kb = options_keyboard([(o["label"], o["id"]) for o in options_data])
    await chat_message.answer(body, reply_markup=kb)


async def _finish_attempt(
    *,
    chat_message: Message,
    state: FSMContext,
    session: AsyncSession,
    attempt_session: AttemptSession,
) -> None:
    await state.clear()
    attempt_service = AttemptService(session)
    finished = await attempt_service.finish(attempt_session)
    is_admin = await AdminService(session).is_admin(chat_message.chat.id)
    user = await UserService(session).get_by_telegram_id(chat_message.chat.id)
    question_count = user.preferred_question_count if user else None

    body = _result_body(
        correct=finished.correct_count,
        total=finished.total_questions,
        cancelled=False,
    )
    await chat_message.answer(
        body,
        reply_markup=main_menu(is_admin=is_admin, question_count=question_count),
    )


# ---- Entry points ------------------------------------------------------------


@router.message(F.text == text.BTN_TAKE_TEST)
async def start_test_flow(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    user = await UserService(session).get_by_telegram_id(message.from_user.id)
    if user is None or not user.is_registered:
        await message.answer(text.NOT_REGISTERED)
        return

    if user.preferred_question_count is None:
        await message.answer(text.CHOOSE_QUESTION_COUNT)
        return

    subjects = await TestService(session).list_active_subjects()
    if not subjects:
        await message.answer(text.NO_SUBJECTS)
        return

    await state.set_state(Testing.choosing_subject)
    await message.answer(text.CHOOSE_SUBJECT, reply_markup=subjects_keyboard(subjects))


@router.callback_query(Testing.choosing_subject, F.data.startswith(SUBJECT_CB_PREFIX))
async def choose_subject(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    assert callback.data is not None
    subject_id = int(callback.data.removeprefix(SUBJECT_CB_PREFIX))

    user = await UserService(session).get_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.answer(text.NOT_REGISTERED, show_alert=True)
        return

    test_service = TestService(session)
    subject = await test_service.get_subject(subject_id)
    if subject is None or not subject.is_active:
        await callback.answer(text.SUBJECT_INACTIVE, show_alert=True)
        return

    if user.preferred_question_count is None:
        await callback.answer(text.CHOOSE_QUESTION_COUNT, show_alert=True)
        return

    attempt_service = AttemptService(session)
    result = await attempt_service.start_or_resume(
        bot_user_id=user.id,
        subject=subject,
        questions_per_attempt=user.preferred_question_count,
    )

    if result.error == AttemptStartError.NO_QUESTIONS:
        await callback.answer()
        await callback.message.edit_text(text.SUBJECT_NO_QUESTIONS)
        is_admin = await AdminService(session).is_admin(callback.from_user.id)
        await callback.message.answer(
            text.MENU_PROMPT,
            reply_markup=main_menu(
                is_admin=is_admin,
                question_count=user.preferred_question_count,
            ),
        )
        await state.clear()
        return

    if result.error == AttemptStartError.INACTIVE_SUBJECT or result.session is None:
        await callback.answer(text.SUBJECT_INACTIVE, show_alert=True)
        return

    await state.update_data(
        subject_id=subject.id,
        bot_user_id=user.id,
        attempt_session_id=result.session.id,
    )

    header_lines = [text.SUBJECT_LABEL.format(name=escape(subject.name))]
    if result.resumed:
        header_lines.append(
            text.ATTEMPT_RESUMED.format(
                n=result.session.attempt_number,
                position=result.session.current_index + 1,
                total=result.session.total_questions,
            )
        )
    else:
        if result.new_round:
            header_lines.append(text.ATTEMPT_NEW_ROUND)
        header_lines.append(
            text.ATTEMPT_STARTED.format(
                n=result.session.attempt_number,
                count=result.session.total_questions,
            )
        )

    await callback.message.edit_text("\n".join(header_lines))
    await callback.answer()
    await _show_current_question(
        chat_message=callback.message,
        state=state,
        session=session,
        attempt_session=result.session,
    )


@router.callback_query(Testing.answering, F.data.startswith(OPTION_CB_PREFIX))
async def answer_question(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    assert callback.data is not None
    selected_option_id = int(callback.data.removeprefix(OPTION_CB_PREFIX))

    data = await state.get_data()
    attempt_session_id: int | None = data.get("attempt_session_id")
    current_question_id: int | None = data.get("current_question_id")
    current_question_text: str = data.get("current_question_text", "")
    subject_id: int | None = data.get("subject_id")
    bot_user_id: int | None = data.get("bot_user_id")
    options_data: list[dict] = list(data.get("current_options", []))
    correct_option_id: int | None = data.get("correct_option_id")

    if (
        not attempt_session_id
        or not current_question_id
        or not subject_id
        or not bot_user_id
        or not options_data
    ):
        await callback.answer(text.SESSION_LOST, show_alert=True)
        await state.clear()
        return

    selected = next((o for o in options_data if o["id"] == selected_option_id), None)
    if selected is None:
        await callback.answer(text.INVALID_OPTION, show_alert=True)
        return

    is_correct = selected["id"] == correct_option_id
    correct_opt = next((o for o in options_data if o["id"] == correct_option_id), None)

    test_service = TestService(session)
    await test_service.record_attempt(
        bot_user_id=bot_user_id,
        subject_id=subject_id,
        question_id=current_question_id,
        selected_option_id=selected_option_id,
        is_correct=is_correct,
        attempt_session_id=attempt_session_id,
    )

    attempt_service = AttemptService(session)
    attempt_session = await attempt_service.get_session(attempt_session_id)
    if attempt_session is None:
        await callback.answer(text.SESSION_LOST, show_alert=True)
        await state.clear()
        return
    attempt_session = await attempt_service.advance(attempt_session, is_correct=is_correct)

    # Текст с вердиктом
    position = attempt_session.current_index  # уже инкрементирован
    total = attempt_session.total_questions
    base = _render_question_text(
        question_text=current_question_text,
        options=options_data,
        position=position,
        total=total,
    )

    if is_correct:
        verdict = "\n\n" + text.CORRECT_VERDICT.format(label=selected["label"])
    else:
        lines = ["", "", text.WRONG_VERDICT_HEADER,
                 text.WRONG_YOU_PICKED.format(label=selected["label"], text=escape(selected["text"]))]
        if correct_opt is not None:
            lines.append(
                text.WRONG_CORRECT_IS.format(
                    label=correct_opt["label"], text=escape(correct_opt["text"])
                )
            )
        verdict = "\n".join(lines)

    await callback.message.edit_text(base + verdict, reply_markup=None)
    await callback.answer()

    # Сброс state-полей текущего вопроса и переход к следующему
    await state.update_data(
        current_question_id=None,
        current_question_text=None,
        current_options=[],
        correct_option_id=None,
    )
    await _show_current_question(
        chat_message=callback.message,
        state=state,
        session=session,
        attempt_session=attempt_session,
    )


@router.callback_query(F.data == CANCEL_TEST_CB)
async def cancel_test(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    data = await state.get_data()
    attempt_session_id: int | None = data.get("attempt_session_id")

    await callback.answer(text.TEST_INTERRUPTED)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    correct = 0
    total = 0
    if attempt_session_id:
        attempt_service = AttemptService(session)
        attempt_session = await attempt_service.get_session(attempt_session_id)
        if attempt_session is not None:
            correct = attempt_session.correct_count
            total = attempt_session.total_questions
            await attempt_service.abort(attempt_session)

    await state.clear()
    is_admin = await AdminService(session).is_admin(callback.from_user.id)
    user = await UserService(session).get_by_telegram_id(callback.from_user.id)
    question_count = user.preferred_question_count if user else None

    if total > 0:
        body = _result_body(correct=correct, total=total, cancelled=True)
    else:
        body = text.MENU_PROMPT
    await callback.message.answer(
        body,
        reply_markup=main_menu(is_admin=is_admin, question_count=question_count),
    )
