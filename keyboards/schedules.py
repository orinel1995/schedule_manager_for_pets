from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


# ---------- /schedules — главное меню расписаний ----------

def schedules_menu_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()

    builder.add(
        KeyboardButton(text="➕ Создать новое расписание"),
    )

    builder.adjust(1)

    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=True
    )


# ---------- Действия с выбранным расписанием ----------

def schedule_actions_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()

    builder.add(
        KeyboardButton(text="✏️ Изменить периодичность"),
        KeyboardButton(text="⛔ Деактивировать"),
        KeyboardButton(text="📋 Выбрать другое"),
    )

    builder.adjust(1)

    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=True
    )


# ---------- Выбор типа расписания ----------

def schedule_type_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()

    builder.add(
        KeyboardButton(text="Каждые Х дней"),
        KeyboardButton(text="Каждую неделю"),
        KeyboardButton(text="Каждый месяц"),
        KeyboardButton(text="Каждый год"),
        KeyboardButton(text="Конкретный день"),
        KeyboardButton(text="❌ Отмена"),
    )

    builder.adjust(1)

    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=True
    )


# ---------- Отмена ввода / подтверждения ----------

def schedule_cancel_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()

    builder.add(
        KeyboardButton(text="❌ Отмена"),
    )

    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=True
    )
