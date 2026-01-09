from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from datetime import date

from keyboards.checklists import today_checklist_keyboard
from data_access.schedule import Schedule
from data_access.checklist import Checklist
from utils.formatters import _format_full_date


router = Router()


@router.message(Command("start"))
async def start_handler(message: Message) -> None:
    """
    /start — приветствие.
    """
    await message.answer(
        "Добро пожаловать домой, снова.\n\n"
        "↙️ Выберите команду через кнопку меню ."
    )


@router.message(Command("today_tasks"))
async def today_tasks_handler(message: Message, state: FSMContext):
    await state.clear()
    user_id = str(message.from_user.id)

    schedule_repo = Schedule(user=user_id)
    checklist_repo = Checklist(user=user_id)

    today_schedules = schedule_repo.get_today()

    if not today_schedules:
        await message.answer(
            "На сегодня заданий нет 🙂",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    checklist_repo.ensure_today_tasks(today_schedules)
    checklist = checklist_repo.get_today()

    await message.answer(
        text=f"Загружено {len(checklist)} заданий.",
        reply_markup=ReplyKeyboardRemove(selective=True)
    )

    await message.answer(
        f"{_format_full_date(date.today().isoformat())}:",
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

    checklist_repo.set_status(checklist_id, not item["status"])
    updated_items = checklist_repo.get_today()

    await callback.message.edit_reply_markup(
        reply_markup=today_checklist_keyboard(updated_items)
    )

    await callback.answer()
