from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


# ---------- /pets — главное меню питомцев ----------

def pets_menu_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()

    builder.add(
        KeyboardButton(text="➕ Создать нового питомца"),
        KeyboardButton(text="📋 Выбрать существующего"),
        KeyboardButton(text="🏠 Главное меню"),
    )

    builder.adjust(1)

    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=True
    )


# ---------- Действия с выбранным питомцем ----------

def pet_actions_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()

    builder.add(
        KeyboardButton(text="✏️ Изменить имя"),
        KeyboardButton(text="✏️ Изменить тип"),
        KeyboardButton(text="📅 Изменить дату рождения"),
        KeyboardButton(text="⛔ Деактивировать"),
        KeyboardButton(text="🏠 Главное меню"),
    )

    builder.adjust(1)

    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=True
    )


# ---------- Подтверждение деактивации ----------

def pet_deactivate_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()

    builder.add(
        KeyboardButton(text="❌ Отмена"),
    )

    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=True
    )


# ---------- Универсальный возврат в главное меню ----------

def cancel_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()

    builder.add(
        KeyboardButton(text="🏠 Главное меню"),
    )

    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=True
    )
