from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def cancel_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="❌ Отмена"),
        KeyboardButton(text="❌ Отключить"),
        )
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
