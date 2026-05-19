from html import escape

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from apps.bot.keyboards.inline import STATS_CB_PREFIX, stats_keyboard
from apps.bot.keyboards.reply import BTN_STATS
from apps.bot.services.admin_service import AdminService
from apps.bot.services.stats_service import (
    StatsPage,
    StatsPeriod,
    StatsService,
    UserStats,
)

router = Router(name="stats")

_PERIOD_LABELS: dict[StatsPeriod, str] = {
    StatsPeriod.WEEK: "Неделя",
    StatsPeriod.MONTH: "Месяц",
    StatsPeriod.YEAR: "Год",
}


def _user_link(user: UserStats) -> str:
    name = escape(user.full_name)
    if user.telegram_username:
        return f'<a href="https://t.me/{user.telegram_username}">{name}</a>'
    return f'<a href="tg://user?id={user.telegram_id}">{name}</a>'


def _format_user(user: UserStats, index: int) -> str:
    lines = [
        f"<b>{index}.</b> {_user_link(user)} — "
        f"{user.correct}/{user.total} ({user.accuracy:.0f}%)"
    ]
    for s in user.by_subject:
        lines.append(f"   • {escape(s.subject_name)}: {s.correct}/{s.total}")
    return "\n".join(lines)


def _format_page(page: StatsPage) -> str:
    label = _PERIOD_LABELS.get(page.period, page.period.value)
    header = (
        f"📊 <b>Статистика — {label}</b>\n"
        f"С {page.since:%Y-%m-%d %H:%M} UTC\n"
        f"Пользователей: <b>{page.total_users}</b> · "
        f"Ответов: <b>{page.total_attempts}</b> · "
        f"Правильных: <b>{page.total_correct}</b>"
    )

    if not page.rows:
        return header + "\n\nПока нет данных за выбранный период."

    body = "\n\n".join(
        _format_user(user, idx)
        for idx, user in enumerate(page.rows, start=page.offset + 1)
    )

    footer = f"\n\nСтраница {page.page_index + 1}/{page.total_pages}"
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
    text = _format_page(page)
    keyboard = stats_keyboard(
        period=page.period,
        offset=page.offset,
        page_size=page.page_size,
        total_users=page.total_users,
    )
    if edit:
        await message.edit_text(text, reply_markup=keyboard, disable_web_page_preview=True)
    else:
        await message.answer(text, reply_markup=keyboard, disable_web_page_preview=True)


@router.message(F.text == BTN_STATS)
async def stats_entry(message: Message, session: AsyncSession) -> None:
    if not await AdminService(session).is_admin(message.from_user.id):
        await message.answer("Команда доступна только администраторам.")
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
        await callback.answer("Только для админов", show_alert=True)
        return

    raw = callback.data.removeprefix(STATS_CB_PREFIX)
    try:
        period_raw, offset_raw = raw.split(":", 1)
        period = StatsPeriod(period_raw)
        offset = int(offset_raw)
    except (ValueError, KeyError):
        await callback.answer("Неверные параметры", show_alert=True)
        return

    await _render_page(
        message=callback.message,
        session=session,
        period=period,
        offset=offset,
        edit=True,
    )
    await callback.answer()
