from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def pets_menu_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()

    builder.add(
        KeyboardButton(text="➕ Создать нового питомца"),
    )

    builder.adjust(1)

    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=True
    )


def pet_actions_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()

    builder.add(
        KeyboardButton(text="✏️ Изменить имя"),
        KeyboardButton(text="✏️ Изменить тип"),
        KeyboardButton(text="📅 Изменить дату рождения"),
        KeyboardButton(text="⛔ Деактивировать"),
        KeyboardButton(text="📋 Выбрать другого"),
    )

    builder.adjust(1)

    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=True
    )


def pet_deactivate_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()

    builder.add(
        KeyboardButton(text="❌ Отмена"),
    )

    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=True
    )
