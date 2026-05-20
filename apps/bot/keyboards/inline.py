from collections.abc import Iterable, Sequence

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from apps.bot import text
from apps.bot.services.stats_service import StatsPeriod
from apps.testing.models.subject import Subject

SUBJECT_CB_PREFIX = "subject:"
OPTION_CB_PREFIX = "opt:"
CANCEL_TEST_CB = "cancel_test"

# format: stats:<period>:<offset>
STATS_CB_PREFIX = "stats:"

MAX_OPTIONS_PER_ROW = 4


def subjects_keyboard(subjects: Iterable[Subject]) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=subject.name,
                callback_data=f"{SUBJECT_CB_PREFIX}{subject.id}",
            )
        ]
        for subject in subjects
    ]
    rows.append(
        [InlineKeyboardButton(text=text.BTN_CANCEL_TEST, callback_data=CANCEL_TEST_CB)]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def options_keyboard(entries: Sequence[tuple[str, int]]) -> InlineKeyboardMarkup:
    """`entries` — упорядоченный список (label, option_id), label вроде "A"/"B"/..."""
    buttons = [
        InlineKeyboardButton(
            text=label,
            callback_data=f"{OPTION_CB_PREFIX}{option_id}",
        )
        for label, option_id in entries
    ]

    rows: list[list[InlineKeyboardButton]] = []
    for i in range(0, len(buttons), MAX_OPTIONS_PER_ROW):
        rows.append(buttons[i : i + MAX_OPTIONS_PER_ROW])

    rows.append(
        [InlineKeyboardButton(text=text.BTN_CANCEL_TEST, callback_data=CANCEL_TEST_CB)]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _stats_cb(period: StatsPeriod, offset: int) -> str:
    return f"{STATS_CB_PREFIX}{period.value}:{offset}"


def stats_keyboard(
    *,
    period: StatsPeriod,
    offset: int,
    page_size: int,
    total_users: int,
) -> InlineKeyboardMarkup:
    period_row = [
        InlineKeyboardButton(
            text=("• " + text.PERIOD_WEEK + " •") if period is StatsPeriod.WEEK else text.PERIOD_WEEK,
            callback_data=_stats_cb(StatsPeriod.WEEK, 0),
        ),
        InlineKeyboardButton(
            text=("• " + text.PERIOD_MONTH + " •") if period is StatsPeriod.MONTH else text.PERIOD_MONTH,
            callback_data=_stats_cb(StatsPeriod.MONTH, 0),
        ),
        InlineKeyboardButton(
            text=("• " + text.PERIOD_YEAR + " •") if period is StatsPeriod.YEAR else text.PERIOD_YEAR,
            callback_data=_stats_cb(StatsPeriod.YEAR, 0),
        ),
    ]

    nav_row: list[InlineKeyboardButton] = []
    if offset > 0:
        prev_offset = max(offset - page_size, 0)
        nav_row.append(
            InlineKeyboardButton(text=text.BTN_PREV, callback_data=_stats_cb(period, prev_offset))
        )
    if offset + page_size < total_users:
        nav_row.append(
            InlineKeyboardButton(
                text=text.BTN_NEXT,
                callback_data=_stats_cb(period, offset + page_size),
            )
        )

    keyboard = [period_row]
    if nav_row:
        keyboard.append(nav_row)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
