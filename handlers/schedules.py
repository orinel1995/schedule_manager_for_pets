from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from datetime import date

from data_access.pet import Pet
from data_access.procedure import Procedure
from data_access.schedule import Schedule
from data_access.checklist import Checklist

from states.schedules import SchedulesStates

from keyboards.schedules import (
    schedules_menu_keyboard,
    schedule_actions_keyboard,
    schedule_type_keyboard,
    schedule_cancel_keyboard,
)

from utils.formatters import (
    format_schedule,
    format_schedules_grouped,
    format_recommendation_date
)

from core.dates import parse_user_date

router = Router()


@router.message(Command("schedules"))
async def schedules_menu_entry(message: Message, state: FSMContext):
    schedule_repo = Schedule(user=str(message.from_user.id))
    schedules = schedule_repo.get_active()

    if not schedules:
        await state.set_state(SchedulesStates.waiting_for_schedule_id)
        await message.answer(
            "Активных расписаний нет.",
            reply_markup=schedules_menu_keyboard(),
        )
        return

    await state.set_state(SchedulesStates.waiting_for_schedule_id)
    await message.answer(
        "Активные расписания:\n\n"
        + format_schedules_grouped(schedules)
        + "\n\n👉 Введите `id` расписания:",
        reply_markup=schedules_menu_keyboard(),
        parse_mode="Markdown"
    )


@router.message(
        SchedulesStates.waiting_for_schedule_id,
        F.text == "➕ Создать новое расписание"
        )
async def schedule_create_start(message: Message, state: FSMContext):
    pet_repo = Pet(user=str(message.from_user.id))
    pets = pet_repo.get_active()

    if not pets:
        await state.set_state(SchedulesStates.waiting_for_schedule_id)
        await message.answer(
            "У вас нет активных питомцев.",
            reply_markup=schedules_menu_keyboard(),
        )
        return

    text = "Выберите питомца:\n\n"
    text += "\n".join(
        f"`{p['id']}`: *{p['name']}* (_{p['type']}_)" for p in pets
        )
    text += "\n\n👉 Введите `id`:"

    await state.set_state(SchedulesStates.waiting_for_pet_id)
    await message.answer(
        text,
        reply_markup=schedule_cancel_keyboard(),
        parse_mode='Markdown'
    )


@router.message(
        SchedulesStates.waiting_for_pet_id,
        ~F.text.startswith("/")
        )
async def schedule_create_pet_selected(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.set_state(SchedulesStates.waiting_for_schedule_id)
        await message.answer(
            "Создание расписания отменено.",
            reply_markup=schedules_menu_keyboard(),
        )
        return

    try:
        pet_id = int(message.text)
    except ValueError:
        await message.answer(
            "`id` должен быть числом.\n\n👉 Попробуйте снова:",
            parse_mode='Markdown')
        return

    pet_repo = Pet(user=str(message.from_user.id))
    pet = pet_repo.get_by_id(pet_id)

    if not pet or not pet["active"]:
        await message.answer(
            "Питомец не найден.\n\n👉 Попробуйте снова:")
        return

    await state.update_data(pet_id=pet_id)

    procedure_repo = Procedure(user=str(message.from_user.id))
    procedures = procedure_repo.get_active()

    if not procedures:
        await state.set_state(SchedulesStates.waiting_for_schedule_id)
        await message.answer(
            "У вас нет активных процедур.\n\nCоздайте новую в /procedures",
            reply_markup=schedules_menu_keyboard(),
        )
        return

    text = "Выберите процедуру:\n\n"
    text += "\n".join(
        f"`{p['id']}`: *{p['name']}*"
        + (f" (_{p['description']}_)" if p.get("description") else "")
        for p in procedures
    )
    text += "\n\n👉 Введите `id`:"

    await state.set_state(SchedulesStates.waiting_for_procedure_id)
    await message.answer(
        text,
        reply_markup=schedule_cancel_keyboard(),
        parse_mode='Markdown'
    )


@router.message(
        SchedulesStates.waiting_for_procedure_id,
        ~F.text.startswith("/")
        )
async def schedule_create_finish(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await message.answer("Создание расписания отменено.")
        schedule_repo = Schedule(user=str(message.from_user.id))
        schedules = schedule_repo.get_active()

        if not schedules:
            await state.set_state(SchedulesStates.waiting_for_schedule_id)
            await message.answer(
                "Активных расписаний нет.",
                reply_markup=schedules_menu_keyboard(),
            )
            return

        await state.set_state(SchedulesStates.waiting_for_schedule_id)
        await message.answer(
            "Активные расписания:\n"
            + format_schedules_grouped(schedules)
            + "\n\n👉 Введите `id` расписания:",
            reply_markup=schedules_menu_keyboard(),
            parse_mode="Markdown"
        )
        return

    try:
        procedure_id = int(message.text)
    except ValueError:
        await message.answer(
            "`id` должен быть числом.\n\n👉 Попробуйте снова:",
            parse_mode="Markdown"
            )
        return

    procedure_repo = Procedure(user=str(message.from_user.id))
    procedure = procedure_repo.get_by_id(procedure_id)

    if not procedure or not procedure["active"]:
        await message.answer(
            "Процедура не найдена.\n\n👉 Попробуйте снова:",
            parse_mode="Markdown"
            )
        return

    data = await state.get_data()
    pet_id = data["pet_id"]

    schedule_repo = Schedule(user=str(message.from_user.id))
    schedule_id = schedule_repo.create(
        pet_id=pet_id,
        procedure_id=procedure_id,
    )

    schedule = schedule_repo.get_by_id(schedule_id)

    await state.update_data(schedule_id=schedule_id)
    await state.set_state(SchedulesStates.edit_select)

    await message.answer(
        "Получено расписание:\n\n"
        + format_schedule(schedule),
        reply_markup=schedule_actions_keyboard(),
        parse_mode='Markdown'
    )


@router.message(
        SchedulesStates.edit_select,
        F.text == "📋 Выбрать другое"
        )
async def schedule_select_start_reverse(message: Message, state: FSMContext):
    schedule_repo = Schedule(user=str(message.from_user.id))
    schedules = schedule_repo.get_active()

    if not schedules:
        await state.set_state(SchedulesStates.waiting_for_schedule_id)
        await message.answer(
            "Активных расписаний нет.",
            reply_markup=schedules_menu_keyboard(),
        )
        return

    await state.set_state(SchedulesStates.waiting_for_schedule_id)
    await message.answer(
        "Активные расписания:\n"
        + format_schedules_grouped(schedules)
        + "\n\n👉 Введите `id` расписания:",
        reply_markup=schedules_menu_keyboard(),
        parse_mode="Markdown"
    )
    return


@router.message(
        SchedulesStates.waiting_for_schedule_id,
        ~F.text.startswith("/")
        )
async def schedule_selected(message: Message, state: FSMContext):
    try:
        schedule_id = int(message.text)
    except ValueError:
        await message.answer(
            "`id` должен быть числом.\n\n👉 Попробуйте снова:",
            parse_mode="Markdown"
            )
        return

    schedule_repo = Schedule(user=str(message.from_user.id))
    schedule = schedule_repo.get_by_id(schedule_id)

    if not schedule or not schedule["active"]:
        await message.answer(
            "Расписание не найдено.\n\n👉 Попробуйте снова:",
            parse_mode="Markdown"
            )
        return

    await state.update_data(schedule_id=schedule_id)
    await state.set_state(SchedulesStates.edit_select)

    await message.answer(
        "Выбрано расписание:\n\n"
        + format_schedule(schedule),
        reply_markup=schedule_actions_keyboard(),
        parse_mode="Markdown"
    )


@router.message(
        SchedulesStates.edit_select,
        F.text == "✏️ Изменить периодичность"
        )
async def schedule_edit_start(message: Message, state: FSMContext):
    await state.set_state(SchedulesStates.waiting_for_schedule_type)
    await message.answer(
        "Выберите тип расписания:",
        reply_markup=schedule_type_keyboard(),
    )


@router.message(
        SchedulesStates.waiting_for_schedule_type,
        ~F.text.startswith("/")
        )
async def schedule_type_selected(message: Message, state: FSMContext):
    date_example = format_recommendation_date(date.today().isoformat())

    mapping_ids = {
        "Каждые Х дней": 1,
        "Каждую неделю": 2,
        "Каждый месяц": 3,
        "Каждый год": 4,
        "Конкретный день": 5,
    }

    mapping_reply = {
        "Каждые Х дней": "Введите число дней между повторениями, например `2`:",
        "Каждую неделю": "Перечислите дни недели через запятую, например `пн, ср, пт`:",
        "Каждый месяц": "Укажите день месяца, например `31`:",
        "Каждый год": f"Укажите дату, например `{date_example}`:",
        "Конкретный день": f"Укажите дату, например `{date_example}`:"
    }

    if message.text == "❌ Отмена":
        await state.set_state(SchedulesStates.edit_select)
        await message.answer(
            "Действие отменено.",
            reply_markup=schedule_actions_keyboard(),
            parse_mode="Markdown"
        )
        return

    if message.text not in mapping_ids:
        return

    await state.update_data(schedule_type_id=mapping_ids[message.text])
    await state.set_state(SchedulesStates.waiting_for_schedule_value)

    await message.answer(
        mapping_reply[message.text],
        reply_markup=schedule_cancel_keyboard(),
        parse_mode="Markdown"
    )


@router.message(
        SchedulesStates.waiting_for_schedule_value,
        ~F.text.startswith("/")
        )
async def schedule_value_entered(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.set_state(SchedulesStates.edit_select)
        await message.answer(
            "Действие отменено.",
            reply_markup=schedule_actions_keyboard(),
        )
        return

    data = await state.get_data()
    schedule_id = data["schedule_id"]
    schedule_type_id = data["schedule_type_id"]

    schedule_repo = Schedule(user=str(message.from_user.id))
    schedule_repo.update_schedule_type(
        schedule_id=schedule_id,
        schedule_type_id=schedule_type_id,
        input_value=message.text.strip(),
    )
    schedules = schedule_repo.get_active()

    if not schedules:
        await state.set_state(SchedulesStates.waiting_for_schedule_id)
        await message.answer(
            "Активных расписаний нет.",
            reply_markup=schedules_menu_keyboard(),
        )
        return

    await state.set_state(SchedulesStates.waiting_for_schedule_id)
    await message.answer(
        "Активные расписания:\n"
        + format_schedules_grouped(schedules)
        + "\n\n👉 Введите `id` расписания:",
        reply_markup=schedules_menu_keyboard(),
        parse_mode="Markdown"
    )


@router.message(
        SchedulesStates.edit_select,
        F.text == "✏️ Изменить начало"
        )
async def schedule_edit_start_date(message: Message, state: FSMContext):
    date_example = format_recommendation_date(date.today().isoformat())

    await state.set_state(SchedulesStates.waiting_for_start_date)
    await message.answer(
        f"Укажите дату, например `{date_example}`:",
        parse_mode='Markdown'
        )


@router.message(
        SchedulesStates.waiting_for_start_date,
        ~F.text.startswith("/")
        )
async def start_date_change_process(message: Message, state: FSMContext):
    parsed = parse_user_date(message.text)
    if parsed is None:
        await message.answer("Не верный формат даты\n\n👉 Попробуйте снова:")
        return

    data = await state.get_data()
    schedule_id = data.get("schedule_id")

    schedule_repo = Schedule(user=str(message.from_user.id))
    schedule_repo.update_start_date(schedule_id, parsed)

    schedule = schedule_repo.get_by_id(schedule_id)
    await state.set_state(SchedulesStates.edit_select)
    await message.answer(
        "Обновлено расписание:\n\n"
        + format_schedule(schedule),
        reply_markup=schedule_actions_keyboard(),
        parse_mode="Markdown"
    )


@router.message(
        SchedulesStates.edit_select,
        F.text == "✏️ Изменить завершение"
        )
async def schedule_edit_end_date(message: Message, state: FSMContext):
    date_example = format_recommendation_date(date.today().isoformat())

    await state.set_state(SchedulesStates.waiting_for_end_date)
    await message.answer(
        f"Укажите дату, например `{date_example}`:",
        parse_mode='Markdown'
        )


@router.message(
        SchedulesStates.waiting_for_end_date,
        ~F.text.startswith("/")
        )
async def end_date_change_process(message: Message, state: FSMContext):
    parsed = parse_user_date(message.text)
    if parsed is None:
        await message.answer("Не верный формат даты\n\n👉 Попробуйте снова:")
        return

    data = await state.get_data()
    schedule_id = data.get("schedule_id")
    schedule_repo = Schedule(user=str(message.from_user.id))
    schedule = schedule_repo.get_by_id(schedule_id)

    start_date_obj = date.fromisoformat(schedule["start_date"])
    parsed_obj = date.fromisoformat(parsed)

    if parsed_obj < start_date_obj:
        await message.answer(
            f"Дата завершения не может быть меньше даты начала "
            f"({format_recommendation_date(schedule['start_date'])})\n\n"
            f"👉 Попробуйте снова:"
        )
        return

    schedule_repo.update_end_date(schedule_id, parsed)

    schedule = schedule_repo.get_by_id(schedule_id)
    await state.set_state(SchedulesStates.edit_select)
    await message.answer(
        "Обновлено расписание:\n\n"
        + format_schedule(schedule),
        reply_markup=schedule_actions_keyboard(),
        parse_mode="Markdown"
    )


@router.message(SchedulesStates.edit_select, F.text == "⛔ Деактивировать")
async def schedule_deactivate_confirm(message: Message, state: FSMContext):
    data = await state.get_data()
    schedule_id = data["schedule_id"]

    schedule_repo = Schedule(user=str(message.from_user.id))
    schedule = schedule_repo.get_by_id(schedule_id)

    await state.set_state(SchedulesStates.deactivate_confirm)
    await message.answer(
        "Вы уверены, что хотите деактивировать расписание?\n\n"
        + format_schedule(schedule)
        + "\n\n👉 Для продолжения введите его `id`:",
        reply_markup=schedule_cancel_keyboard(),
        parse_mode="Markdown"
    )


@router.message(
        SchedulesStates.deactivate_confirm,
        ~F.text.startswith("/")
        )
async def schedule_deactivate_process(message: Message, state: FSMContext):
    data = await state.get_data()
    schedule_id = data["schedule_id"]

    if message.text == "❌ Отмена" or message.text != str(schedule_id):
        await state.set_state(SchedulesStates.edit_select)
        await message.answer(
            "Действие отменено.",
            reply_markup=schedule_actions_keyboard(),
        )
        return

    schedule_repo = Schedule(user=str(message.from_user.id))
    schedule_repo.set_active(schedule_id, False)

    checklist_repo = Checklist(user=str(message.from_user.id))
    checklist_repo.update_inactive()

    schedules = schedule_repo.get_active()

    if not schedules:
        await state.set_state(SchedulesStates.waiting_for_schedule_id)
        await message.answer(
            "Активных расписаний нет.",
            reply_markup=schedules_menu_keyboard(),
        )
        return

    await state.set_state(SchedulesStates.waiting_for_schedule_id)
    await message.answer(
        "Активные расписания:\n"
        + format_schedules_grouped(schedules)
        + "\n\n👉 Введите `id` расписания:",
        reply_markup=schedules_menu_keyboard(),
        parse_mode="Markdown"
    )
