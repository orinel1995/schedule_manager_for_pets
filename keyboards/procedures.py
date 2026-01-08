from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


# ---------- /procedures — главное меню процедур ----------

def procedures_menu_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()

    builder.add(
        KeyboardButton(text="➕ Создать новую процедуру"),
        KeyboardButton(text="📋 Выбрать существующую"),
        KeyboardButton(text="🏠 Главное меню"),
    )

    builder.adjust(1)

    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=True
    )


# ---------- Действия с выбранной процедурой ----------

def procedure_actions_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()

    builder.add(
        KeyboardButton(text="✏️ Изменить описание"),
        KeyboardButton(text="⛔ Деактивировать"),
        KeyboardButton(text="🏠 Главное меню"),
    )

    builder.adjust(1)

    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=True
    )


# ---------- Подтверждение деактивации ----------

def procedure_cancel_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()

    builder.add(
        KeyboardButton(text="❌ Отмена"),
    )

    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=True
    )


# ---------- Универсальный возврат в главное меню ----------

def main_menu_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()

    builder.add(
        KeyboardButton(text="🏠 Главное меню"),
    )

    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=True
    )
