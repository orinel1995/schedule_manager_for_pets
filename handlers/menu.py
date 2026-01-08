from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from states.pets import PetsStates
from keyboards.pets import pets_menu_keyboard
from states.procedures import ProcedureStates
from keyboards.procedures import procedures_menu_keyboard
from states.schedules import SchedulesStates
from keyboards.schedules import schedules_menu_keyboard
from keyboards.checklists import today_checklist_keyboard
from data_access.schedule import Schedule
from data_access.checklist import Checklist

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


@router.message(F.text == "📅 Управление расписаниями")
async def schedules_menu_entry(message: Message, state: FSMContext) -> None:
    """
    Переход в меню управления расписаниями.
    """
    await state.set_state(SchedulesStates.action_select)

    await message.answer(
        "Выберите действие:",
        reply_markup=schedules_menu_keyboard()
    )


@router.message(F.text == "📋 Задания на сегодня")
async def today_tasks_handler(message: Message):
    user_id = str(message.from_user.id)

    schedule_repo = Schedule(user=user_id)
    checklist_repo = Checklist(user=user_id)

    # 1. Получаем расписания на сегодня
    today_schedules = schedule_repo.get_today()

    if not today_schedules:
        await message.answer(
            "На сегодня заданий нет 🙂",
            reply_markup=main_menu_keyboard()
        )
        return

    # 2. Инициализируем чеклист (без перезаписи существующих)
    checklist_repo.ensure_today_tasks(today_schedules)

    # 3. Получаем чеклист со статусами
    checklist = checklist_repo.get_today()

    # 4. Отправляем inline-чеклист
    await message.answer(
        "Задания на сегодня:",
        reply_markup=today_checklist_keyboard(checklist),
    )


@router.callback_query(F.data.startswith("checklist_toggle:"))
async def checklist_toggle_handler(callback, state):
    checklist_id = int(callback.data.split(":")[1])
    user_id = str(callback.from_user.id)

    checklist_repo = Checklist(user=user_id)

    items = checklist_repo.get_today()
    item = next(i for i in items if i["id"] == checklist_id)

    # инвертируем статус
    checklist_repo.set_status(checklist_id, not item["status"])

    # обновляем клавиатуру
    updated_items = checklist_repo.get_today()

    await callback.message.edit_reply_markup(
        reply_markup=today_checklist_keyboard(updated_items)
    )

    await callback.answer()
