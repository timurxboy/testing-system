from html import escape

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from apps.bot import text
from apps.bot.keyboards.inline import STATS_CB_PREFIX, stats_keyboard
from apps.bot.models.attempt_session import AttemptSessionStatus
from apps.bot.services.admin_service import AdminService
from apps.bot.services.stats_service import (
    AttemptStat,
    StatsPage,
    StatsPeriod,
    StatsService,
    UserStats,
)

router = Router(name="stats")

_PERIOD_LABELS: dict[StatsPeriod, str] = {
    StatsPeriod.WEEK: text.PERIOD_WEEK,
    StatsPeriod.MONTH: text.PERIOD_MONTH,
    StatsPeriod.YEAR: text.PERIOD_YEAR,
}


def _user_link(user: UserStats) -> str:
    name = escape(user.display_name)
    if user.telegram_username:
        return f'<a href="https://t.me/{user.telegram_username}">{name}</a>'
    return f'<a href="tg://user?id={user.telegram_id}">{name}</a>'


def _grade_for(percent: float) -> str:
    if percent >= 90:
        return text.GRADE_EXCELLENT
    if percent >= 80:
        return text.GRADE_GOOD
    if percent >= 70:
        return text.GRADE_SATISFACTORY
    return text.GRADE_UNSATISFACTORY


def _format_attempt(attempt: AttemptStat) -> str:
    cancelled = (
        text.STATS_ATTEMPT_CANCELLED
        if attempt.status is AttemptSessionStatus.ABORTED
        else ""
    )
    return text.STATS_ATTEMPT_LINE.format(
        subject=escape(attempt.subject_name),
        n=attempt.attempt_number,
        correct=attempt.correct,
        total=attempt.total,
        percent=attempt.accuracy,
        grade=_grade_for(attempt.accuracy),
        cancelled=cancelled,
    )


def _format_user(user: UserStats, index: int) -> str:
    header = text.STATS_USER_HEADER.format(
        idx=index, link=_user_link(user), attempts=user.total_attempts
    )
    if not user.attempts:
        return header
    lines = [header]
    lines.extend(_format_attempt(a) for a in user.attempts)
    return "\n".join(lines)


def _format_page(page: StatsPage) -> str:
    label = _PERIOD_LABELS.get(page.period, page.period.value)
    header = (
        text.STATS_HEADER.format(period=label)
        + "\n"
        + text.STATS_SINCE.format(since=page.since)
        + "\n"
        + text.STATS_TOTALS.format(users=page.total_users)
    )

    if not page.rows:
        return header + "\n\n" + text.STATS_NO_DATA

    body = "\n\n".join(
        _format_user(user, idx)
        for idx, user in enumerate(page.rows, start=page.offset + 1)
    )
    footer = "\n\n" + text.STATS_PAGE.format(
        n=page.page_index + 1, total=page.total_pages
    )
    return f"{header}\n\n{body}{footer}"


async def _render_page(
    *,
    message: Message,
    session: AsyncSession,
    period: StatsPeriod,
    offset: int,
    edit: bool,
) -> None:
    page = await StatsService(session).fetch_page(period, offset=offset)
    body = _format_page(page)
    kb = stats_keyboard(
        period=page.period,
        offset=page.offset,
        page_size=page.page_size,
        total_users=page.total_users,
    )
    if edit:
        await message.edit_text(body, reply_markup=kb, disable_web_page_preview=True)
    else:
        await message.answer(body, reply_markup=kb, disable_web_page_preview=True)


@router.message(F.text == text.BTN_STATS)
async def stats_entry(message: Message, session: AsyncSession) -> None:
    if not await AdminService(session).is_admin(message.from_user.id):
        await message.answer(text.ONLY_FOR_ADMINS)
        return

    await _render_page(
        message=message,
        session=session,
        period=StatsPeriod.WEEK,
        offset=0,
        edit=False,
    )


@router.callback_query(F.data.startswith(STATS_CB_PREFIX))
async def stats_navigate(callback: CallbackQuery, session: AsyncSession) -> None:
    assert callback.data is not None

    if not await AdminService(session).is_admin(callback.from_user.id):
        await callback.answer(text.ONLY_FOR_ADMINS, show_alert=True)
        return

    raw = callback.data.removeprefix(STATS_CB_PREFIX)
    try:
        period_raw, offset_raw = raw.split(":", 1)
        period = StatsPeriod(period_raw)
        offset = int(offset_raw)
    except (ValueError, KeyError):
        await callback.answer("Invalid params", show_alert=True)
        return

    await _render_page(
        message=callback.message,
        session=session,
        period=period,
        offset=offset,
        edit=True,
    )
    await callback.answer()
