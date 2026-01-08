from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from data_access.procedure import Procedure
from states.procedures import ProcedureStates
from keyboards.procedures import (
    procedures_menu_keyboard,
    procedure_actions_keyboard,
    procedure_cancel_keyboard,
    main_menu_keyboard,
)
from utils.formatters import format_procedure

router = Router()


@router.message(F.text == "🧪 Управление процедурами")
async def procedures_menu(message: Message, state: FSMContext):
    await state.set_state(ProcedureStates.action_select)
    await message.answer(
        "Выберите действие:",
        reply_markup=procedures_menu_keyboard(),
    )


@router.message(ProcedureStates.action_select, F.text == "➕ Создать новую процедуру")
async def procedure_create_start(message: Message, state: FSMContext):
    await state.set_state(ProcedureStates.waiting_for_name)
    await message.answer(
        "Введите название процедуры:",
        reply_markup=procedure_cancel_keyboard(),
    )


@router.message(ProcedureStates.waiting_for_name)
async def procedure_create_finish(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.set_state(ProcedureStates.action_select)
        await message.answer(
            "Действие отменено.",
            reply_markup=procedures_menu_keyboard(),
            )
        return

    procedure_repo = Procedure(user=str(message.from_user.id))

    procedure_id = procedure_repo.create(
        name=message.text.strip()
    )
    procedure = procedure_repo.get_by_id(procedure_id)

    await state.set_state(ProcedureStates.action_select)
    await state.update_data(procedure_id=procedure_id)

    await message.answer(
        format_procedure(procedure),
        reply_markup=procedure_actions_keyboard(),
    )


@router.message(ProcedureStates.action_select, F.text == "📋 Выбрать существующую")
async def procedure_select(message: Message, state: FSMContext):
    procedure_repo = Procedure(user=str(message.from_user.id))
    procedures = procedure_repo.get_active()

    if not procedures:
        await message.answer(
            "Активные процедур нет.",
            reply_markup=procedures_menu_keyboard(),
        )
        return

    procedures.sort(key=lambda p: p["id"])

    text = "Активные процедуры:\n\n"
    text += "\n".join(
        f"{p['id']}: {p['name']}"
        + (f" ({p['description']})" if p.get("description") else "")
        for p in procedures
    )
    text += "\n\nНапишите id процедуры:"

    await state.set_state(ProcedureStates.waiting_for_id)
    await message.answer(
        text,
        reply_markup=procedure_cancel_keyboard(),
    )


@router.message(ProcedureStates.waiting_for_id)
async def procedure_open(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.set_state(ProcedureStates.action_select)
        await message.answer(
            "Действие отменено.",
            reply_markup=procedures_menu_keyboard(),
            )
        return

    try:
        procedure_id = int(message.text)
    except ValueError:
        await message.answer("id должен быть числом.")
        return

    procedure_repo = Procedure(user=str(message.from_user.id))
    procedure = procedure_repo.get_by_id(procedure_id)

    if not procedure:
        await message.answer("Процедура не найдена.")
        return

    await state.set_state(ProcedureStates.action_select)
    await state.update_data(procedure_id=procedure_id)

    await message.answer(
        format_procedure(procedure),
        reply_markup=procedure_actions_keyboard(),
    )


@router.message(ProcedureStates.action_select, F.text == "✏️ Изменить описание")
async def procedure_edit_description_start(message: Message, state: FSMContext):
    await state.set_state(ProcedureStates.waiting_for_description)
    await message.answer(
        "Введите описание процедуры:",
        reply_markup=procedure_cancel_keyboard(),
    )


@router.message(ProcedureStates.waiting_for_description)
async def procedure_edit_description_finish(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.set_state(ProcedureStates.action_select)
        await message.answer(
            "Действие отменено.",
            reply_markup=procedures_menu_keyboard(),
            )
        return

    data = await state.get_data()
    procedure_id = data.get("procedure_id")

    procedure_repo = Procedure(user=str(message.from_user.id))
    procedure_repo.update_description(
        procedure_id,
        message.text.strip(),
    )

    procedure = procedure_repo.get_by_id(procedure_id)

    await state.set_state(ProcedureStates.action_select)

    await message.answer(
        format_procedure(procedure),
        reply_markup=procedure_actions_keyboard(),
    )


@router.message(ProcedureStates.action_select, F.text == "⛔ Деактивировать")
async def procedure_deactivate_confirm(message: Message, state: FSMContext):
    data = await state.get_data()
    procedure_id = data["procedure_id"]

    procedure_repo = Procedure(user=str(message.from_user.id))
    procedure = procedure_repo.get_by_id(procedure_id)

    await state.set_state(ProcedureStates.deactivate_confirm)

    await message.answer(
        "Вы уверены, что хотите деактивировать процедуру?\n\n"
        + format_procedure(procedure)
        + "\n\nДля продолжения введите её id:",
        reply_markup=procedure_cancel_keyboard(),
    )


@router.message(ProcedureStates.deactivate_confirm)
async def procedure_deactivate_process(message: Message, state: FSMContext):
    data = await state.get_data()
    procedure_id = data["procedure_id"]

    if message.text == "❌ Отмена" or message.text != str(procedure_id):
        await state.set_state(ProcedureStates.action_select)
        await message.answer(
            "Деактивация отменена.",
            reply_markup=procedures_menu_keyboard(),
            )
        return

    procedure_repo = Procedure(user=str(message.from_user.id))
    procedure_repo.update_active(procedure_id, False)

    procedure = procedure_repo.get_by_id(procedure_id)
    await state.clear()

    await message.answer(
        "Процедура деактивирована:\n\n" + format_procedure(procedure),
        reply_markup=main_menu_keyboard(),
    )
