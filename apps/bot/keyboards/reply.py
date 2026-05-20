from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

from apps.bot import text


def main_menu(*, is_admin: bool) -> ReplyKeyboardMarkup:
    rows: list[list[KeyboardButton]] = [[KeyboardButton(text=text.BTN_TAKE_TEST)]]
    if is_admin:
        rows.append([KeyboardButton(text=text.BTN_STATS)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()
