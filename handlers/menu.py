from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from datetime import date, datetime
from collections import defaultdict

from keyboards.menus import cancel_keyboard
from keyboards.checklists import procedure_checklist_keyboard

from data_access.schedule import Schedule
from data_access.checklist import Checklist
from data_access.notification import Notification

from utils.formatters import _format_full_date

from states.menus import MenuStates

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
    checklist_complition = checklist_repo.get_last_week_completion()

    complition: list[str] = [
        "•" if result[1] == 1 else "∙"
        for result in checklist_complition
    ]

    await message.answer(
        f"Задания на {_format_full_date(date.today().isoformat())}:\n"
        f"{' '.join(complition)}",
        reply_markup=ReplyKeyboardRemove()
    )

    # группируем по процедуре
    grouped: dict[int, list[dict]] = defaultdict(list)
    for item in checklist:
        grouped[item["procedure_id"]].append(item)

    # отправляем отдельное сообщение на каждую процедуру
    for items in grouped.values():
        first = items[0]

        text = f"*{first['procedure_name']}*"
        if first.get("procedure_description"):
            text += f" (_{first['procedure_description']}_)"
        text += ":"
        await message.answer(
            text=text,
            reply_markup=procedure_checklist_keyboard(items),
            parse_mode="Markdown"
        )


@router.callback_query(F.data.startswith("checklist_toggle:"))
async def checklist_toggle_handler(callback: CallbackQuery):
    checklist_id = int(callback.data.split(":")[1])
    user_id = str(callback.from_user.id)

    checklist_repo = Checklist(user=user_id)

    items = checklist_repo.get_today()
    item = next((i for i in items if i["id"] == checklist_id), None)

    if item is None:
        await callback.answer(
            "Этот чеклист устарел. Откройте задания на сегодня.",
            show_alert=False,
        )
        return

    checklist_repo.set_status(checklist_id, not item["status"])

    # берём обновлённые элементы ТОЛЬКО этой процедуры
    updated_items = [
        i for i in checklist_repo.get_today()
        if i["procedure_id"] == item["procedure_id"]
    ]

    await callback.message.edit_reply_markup(
        reply_markup=procedure_checklist_keyboard(updated_items)
    )

    await callback.answer()


@router.message(Command("reminder"))
async def notification_handler(message: Message, state: FSMContext):
    await state.clear()

    user_id = str(message.from_user.id)
    notification_repo = Notification(user=user_id)

    current_value = notification_repo.get_user_notification()

    if current_value:
        text = (
            f"Текущее время напоминания: *{current_value}*\n\n"
            "👉 Введите новое время, например `21:00`:"
        )
    else:
        text = (
            "У вас не установлено напоминание.\n\n"
            "👉 Введите новое время, например `21:00`:"
        )

    await state.set_state(MenuStates.update_time_waiting_input)

    await message.answer(
        text,
        reply_markup=cancel_keyboard(),
        parse_mode="Markdown"
    )


@router.message(
    MenuStates.update_time_waiting_input,
    ~F.text.startswith("/")
)
async def notification_update_process(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    text = message.text.strip()

    if text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "Действие отменено.",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    if text == "❌ Отключить":
        notification_repo = Notification(user=user_id)
        notification_repo.set_new_notification(None)

        await state.clear()
        await message.answer(
            "Напоминание отключено.",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="Markdown"
        )
        return

    try:
        # строгая проверка формата HH:MM
        parsed_time = datetime.strptime(text, "%H:%M").strftime("%H:%M")
    except ValueError:
        await message.answer(
            "Неверный формат времени, попробуйте еще раз."
        )
        return

    notification_repo = Notification(user=user_id)
    notification_repo.set_new_notification(parsed_time)

    await state.clear()
    await message.answer(
        f"Время *{parsed_time}* сохранено.",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown"
    )
