from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from states.pets import PetsStates
from keyboards.pets import pets_menu_keyboard
from states.procedures import ProcedureStates
from keyboards.procedures import procedures_menu_keyboard


router = Router()


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Главное меню бота.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🐾 Управление питомцами")],
            [KeyboardButton(text="🧪 Управление процедурами")],
            [KeyboardButton(text="📅 Управление расписаниями")],
            [KeyboardButton(text="📋 Задания на сегодня")],
        ],
        resize_keyboard=True
    )


@router.message(Command("start"))
async def start_handler(message: Message) -> None:
    """
    /start — главное меню.
    """
    await message.answer(
        "Выберите категорию:",
        reply_markup=main_menu_keyboard()
    )


@router.message(Command("menu"))
async def menu_handler(message: Message) -> None:
    """
    /menu — главное меню.
    """
    await message.answer(
        "Выберите категорию:",
        reply_markup=main_menu_keyboard()
    )


@router.message(F.text == "🐾 Управление питомцами")
async def pets_menu_entry(message: Message, state) -> None:
    """
    Переход в меню управления питомцами.
    """
    await state.set_state(PetsStates.action_select)

    await message.answer(
        "Выберите действие:",
        reply_markup=pets_menu_keyboard()
    )


@router.message(F.text == "🏠 Главное меню")
async def back_to_main_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await menu_handler(message)


@router.message(F.text == "🧪 Управление процедурами")
async def procedures_menu_entry(message: Message, state: FSMContext) -> None:
    """
    Переход в меню управления процедурами.
    """
    await state.set_state(ProcedureStates.action_select)

    await message.answer(
        "Выберите действие:",
        reply_markup=procedures_menu_keyboard()
    )

# --- Заглушки под будущие разделы (чтобы не было 'Update not handled') ---


@router.message(F.text == "📅 Управление расписаниями")
async def schedules_stub(message: Message) -> None:
    await message.answer("Раздел «Расписания» в разработке.")


@router.message(F.text == "📋 Задания на сегодня")
async def today_stub(message: Message) -> None:
    await message.answer("Раздел «Задания на сегодня» в разработке.")
