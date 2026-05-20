from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

from apps.bot import text


def main_menu(*, is_admin: bool, question_count: int | None = None) -> ReplyKeyboardMarkup:
    rows: list[list[KeyboardButton]] = [[KeyboardButton(text=text.BTN_TAKE_TEST)]]
    if question_count is not None:
        rows.append(
            [
                KeyboardButton(
                    text=text.BTN_QUESTION_COUNT_TEMPLATE.format(count=question_count)
                )
            ]
        )
    if is_admin:
        rows.append([KeyboardButton(text=text.BTN_STATS)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()
