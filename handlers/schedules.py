from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from data_access.pet import Pet
from data_access.procedure import Procedure
from data_access.schedule import Schedule

from states.schedules import SchedulesStates

from keyboards.schedules import (
    schedules_menu_keyboard,
    schedule_actions_keyboard,
    schedule_type_keyboard,
    schedule_cancel_keyboard,
)

from keyboards.pets import cancel_keyboard as main_menu_keyboard

from utils.formatters import (
    format_schedule,
    format_schedules_grouped,
)

router = Router()


# ---------- ВХОД В МЕНЮ РАСПИСАНИЙ ----------

@router.message(F.text == "📅 Управление расписаниями")
async def schedules_menu_entry(message: Message, state: FSMContext):
    await state.set_state(SchedulesStates.action_select)
    await message.answer(
        "Выберите действие:",
        reply_markup=schedules_menu_keyboard(),
    )


# ---------- СОЗДАНИЕ РАСПИСАНИЯ ----------

@router.message(SchedulesStates.action_select, F.text == "➕ Создать расписание")
async def schedule_create_start(message: Message, state: FSMContext):
    pet_repo = Pet(user=str(message.from_user.id))
    pets = pet_repo.get_active()

    if not pets:
        await state.set_state(SchedulesStates.action_select)
        await message.answer(
            "У вас нет активных питомцев.",
            reply_markup=schedules_menu_keyboard(),
        )
        return

    text = "Выберите питомца:\n\n"
    text += "\n".join(f"{p['id']}: {p['name']}" for p in pets)
    text += "\n\nВведите id:"

    await state.set_state(SchedulesStates.waiting_for_pet_id)
    await message.answer(
        text,
        reply_markup=schedule_cancel_keyboard(),
    )


@router.message(SchedulesStates.waiting_for_pet_id)
async def schedule_create_pet_selected(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.set_state(SchedulesStates.action_select)
        await message.answer(
            "Действие отменено.",
            reply_markup=schedules_menu_keyboard(),
        )
        return

    try:
        pet_id = int(message.text)
    except ValueError:
        await message.answer("id должен быть числом. Попробуйте снова:")
        return

    pet_repo = Pet(user=str(message.from_user.id))
    pet = pet_repo.get_by_id(pet_id)

    if not pet or not pet["active"]:
        await message.answer("Питомец не найден. Попробуйте снова:")
        return

    await state.update_data(pet_id=pet_id)

    procedure_repo = Procedure(user=str(message.from_user.id))
    procedures = procedure_repo.get_active()

    if not procedures:
        await state.set_state(SchedulesStates.action_select)
        await message.answer(
            "У вас нет активных процедур.",
            reply_markup=schedules_menu_keyboard(),
        )
        return

    text = "Выберите процедуру:\n\n"
    text += "\n".join(
        f"{p['id']}: {p['name']}"
        + (f" ({p['description']})" if p.get("description") else "")
        for p in procedures
    )
    text += "\n\nВведите id:"

    await state.set_state(SchedulesStates.waiting_for_procedure_id)
    await message.answer(
        text,
        reply_markup=schedule_cancel_keyboard(),
    )


@router.message(SchedulesStates.waiting_for_procedure_id)
async def schedule_create_finish(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.set_state(SchedulesStates.action_select)
        await message.answer(
            "Действие отменено.",
            reply_markup=schedules_menu_keyboard(),
        )
        return

    try:
        procedure_id = int(message.text)
    except ValueError:
        await message.answer("id должен быть числом. Попробуйте снова:")
        return

    procedure_repo = Procedure(user=str(message.from_user.id))
    procedure = procedure_repo.get_by_id(procedure_id)

    if not procedure or not procedure["active"]:
        await message.answer("Процедура не найдена. Попробуйте снова:")
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
        "Получено расписание:\n\n" + format_schedule(schedule),
        reply_markup=schedule_actions_keyboard(),
    )


# ---------- ВЫБОР СУЩЕСТВУЮЩЕГО ----------

@router.message(SchedulesStates.action_select, F.text == "📋 Выбрать существующее")
async def schedule_select_start(message: Message, state: FSMContext):
    schedule_repo = Schedule(user=str(message.from_user.id))
    schedules = schedule_repo.get_active()

    if not schedules:
        await state.set_state(SchedulesStates.action_select)
        await message.answer(
            "Активных расписаний нет.",
            reply_markup=schedules_menu_keyboard(),
        )
        return

    await state.set_state(SchedulesStates.waiting_for_schedule_id)
    await message.answer(
        format_schedules_grouped(schedules) + "\n\nВведите id расписания:",
        reply_markup=schedule_cancel_keyboard(),
    )


@router.message(SchedulesStates.waiting_for_schedule_id)
async def schedule_selected(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.set_state(SchedulesStates.action_select)
        await message.answer(
            "Действие отменено.",
            reply_markup=schedules_menu_keyboard(),
        )
        return

    try:
        schedule_id = int(message.text)
    except ValueError:
        await message.answer("id должен быть числом.")
        return

    schedule_repo = Schedule(user=str(message.from_user.id))
    schedule = schedule_repo.get_by_id(schedule_id)

    if not schedule or not schedule["active"]:
        await message.answer("Расписание не найдено.")
        return

    await state.update_data(schedule_id=schedule_id)
    await state.set_state(SchedulesStates.edit_select)

    await message.answer(
        format_schedule(schedule),
        reply_markup=schedule_actions_keyboard(),
    )


# ---------- РЕДАКТИРОВАНИЕ ----------

@router.message(SchedulesStates.edit_select, F.text == "✏️ Изменить периодичность")
async def schedule_edit_start(message: Message, state: FSMContext):
    await state.set_state(SchedulesStates.waiting_for_schedule_type)
    await message.answer(
        "Выберите тип расписания:",
        reply_markup=schedule_type_keyboard(),
    )


@router.message(SchedulesStates.waiting_for_schedule_type)
async def schedule_type_selected(message: Message, state: FSMContext):
    mapping = {
        "Каждые Х дней": 1,
        "Каждую неделю": 2,
        "Каждый месяц": 3,
        "Каждый год": 4,
        "Конкретный день": 5,
    }

    if message.text == "❌ Отмена":
        await state.set_state(SchedulesStates.edit_select)
        await message.answer(
            "Действие отменено.",
            reply_markup=schedule_actions_keyboard(),
        )
        return

    if message.text not in mapping:
        return

    await state.update_data(schedule_type_id=mapping[message.text])
    await state.set_state(SchedulesStates.waiting_for_schedule_value)

    await message.answer(
        "Введите значение для выбранного типа:",
        reply_markup=schedule_cancel_keyboard(),
    )


@router.message(SchedulesStates.waiting_for_schedule_value)
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
    schedule_repo.update_schedule(
        schedule_id=schedule_id,
        schedule_type_id=schedule_type_id,
        input_value=message.text.strip(),
    )

    await state.set_state(SchedulesStates.action_select)
    await message.answer(
        "Расписание обновлено.",
        reply_markup=schedules_menu_keyboard(),
    )


# ---------- ДЕАКТИВАЦИЯ ----------

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
        + "\n\nДля продолжения введите его id:",
        reply_markup=schedule_cancel_keyboard(),
    )


@router.message(SchedulesStates.deactivate_confirm)
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

    schedule = schedule_repo.get_by_id(schedule_id)
    await state.clear()

    await message.answer(
        "Расписание деактивировано:\n\n" + format_schedule(schedule),
        reply_markup=schedules_menu_keyboard(),
    )


# ---------- ВОЗВРАТ В ГЛАВНОЕ МЕНЮ ----------

@router.message(F.text == "🏠 Главное меню")
async def back_to_main_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Выберите категорию:",
        reply_markup=main_menu_keyboard(),
    )
