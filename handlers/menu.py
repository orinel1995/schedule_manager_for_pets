from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from datetime import date

from states.pets import PetsStates
from keyboards.pets import pets_menu_keyboard
from states.procedures import ProcedureStates
from keyboards.procedures import procedures_menu_keyboard
from states.schedules import SchedulesStates
from keyboards.schedules import schedules_menu_keyboard
from keyboards.checklists import today_checklist_keyboard
from data_access.schedule import Schedule
from data_access.checklist import Checklist
from utils.formatters import _format_full_date


router = Router()


@router.message(Command("start"))
async def start_handler(message: Message) -> None:
    """
    /start — главное меню.
    """
    await message.answer(
        "Добро пожаловать домой, снова.\n\n"
        "Выберите команду через кнопку меню."
    )


@router.message(Command("pets"))
async def pets_menu_entry(message: Message, state: FSMContext) -> None:
    """
    Переход в меню управления питомцами.
    """
    await state.set_state(PetsStates.action_select)

    await message.answer(
        "Выберите действие:",
        reply_markup=pets_menu_keyboard()
    )


@router.message(Command("procedures"))
async def procedures_menu_entry(message: Message, state: FSMContext) -> None:
    """
    Переход в меню управления процедурами.
    """
    await state.set_state(ProcedureStates.action_select)

    await message.answer(
        "Выберите действие:",
        reply_markup=procedures_menu_keyboard()
    )


@router.message(Command("schedules"))
async def schedules_menu_entry(message: Message, state: FSMContext) -> None:
    """
    Переход в меню управления расписаниями.
    """
    await state.set_state(SchedulesStates.action_select)

    await message.answer(
        "Выберите действие:",
        reply_markup=schedules_menu_keyboard()
    )


@router.message(Command("today_tasks"))
async def today_tasks_handler(message: Message):
    user_id = str(message.from_user.id)

    schedule_repo = Schedule(user=user_id)
    checklist_repo = Checklist(user=user_id)

    # 1. Получаем расписания на сегодня
    today_schedules = schedule_repo.get_today()

    if not today_schedules:
        await message.answer(
            "На сегодня заданий нет 🙂"
        )
        return

    # 2. Инициализируем чеклист (без перезаписи существующих)
    checklist_repo.ensure_today_tasks(today_schedules)

    # 3. Получаем чеклист со статусами
    checklist = checklist_repo.get_today()

    # 4. Отправляем inline-чеклист
    await message.answer(
        f"Задания на {_format_full_date(date.today().isoformat())}:",
        reply_markup=today_checklist_keyboard(checklist),
    )


@router.callback_query(F.data.startswith("checklist_toggle:"))
async def checklist_toggle_handler(callback):
    checklist_id = int(callback.data.split(":")[1])
    user_id = str(callback.from_user.id)

    checklist_repo = Checklist(user=user_id)

    items = checklist_repo.get_today()
    item = next(
        (i for i in items if i["id"] == checklist_id),
        None
    )

    if item is None:
        await callback.answer(
            "Этот чеклист устарел. Откройте задания на сегодня.",
            show_alert=False,
        )
        return

    # инвертируем статус
    checklist_repo.set_status(checklist_id, not item["status"])

    # обновляем клавиатуру
    updated_items = checklist_repo.get_today()

    await callback.message.edit_reply_markup(
        reply_markup=today_checklist_keyboard(updated_items)
    )

    await callback.answer()
