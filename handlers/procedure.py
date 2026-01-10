from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from data_access.procedure import Procedure
from states.procedures import ProcedureStates
from keyboards.procedures import (
    procedures_menu_keyboard,
    procedure_actions_keyboard,
    procedure_cancel_keyboard,
)
from utils.formatters import format_procedure

router = Router()


@router.message(Command("procedures"))
async def procedures_menu(message: Message, state: FSMContext):
    procedure_repo = Procedure(user=str(message.from_user.id))
    procedures = procedure_repo.get_active()

    if not procedures:
        await state.set_state(ProcedureStates.waiting_for_id)
        await message.answer(
            "Активных процедур нет.",
            reply_markup=procedures_menu_keyboard(),
        )
        return

    text = "Активные процедуры:\n"
    text += "────────────────\n"
    text += "\n".join(
        f"`{p['id']}`: *{p['name']}*"
        + (f" (_{p['description']}_)" if p.get("description") else "")
        for p in procedures
    )
    text += "\n\n👉 Введите `id` процедуры:"

    await state.set_state(ProcedureStates.waiting_for_id)
    await message.answer(
        text,
        reply_markup=procedures_menu_keyboard(),
        parse_mode='Markdown'
    )


@router.message(
        ProcedureStates.waiting_for_id,
        F.text == "➕ Создать новую процедуру"
        )
async def procedure_create_start(message: Message, state: FSMContext):
    await state.set_state(ProcedureStates.waiting_for_name)
    await message.answer(
        "Введите название процедуры:",
        reply_markup=procedure_cancel_keyboard(),
    )


@router.message(
        ProcedureStates.waiting_for_name,
        ~F.text.startswith("/")
        )
async def procedure_create_finish(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.set_state(ProcedureStates.waiting_for_id)
        await message.answer(
            "Создание процедуры отменено.",
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
        "Получена процедура:\n\n"
        + format_procedure(procedure),
        reply_markup=procedure_actions_keyboard(),
        parse_mode='Markdown'
    )


@router.message(ProcedureStates.action_select, F.text == "📋 Выбрать другую")
async def procedure_select_reverse(message: Message, state: FSMContext):
    procedure_repo = Procedure(user=str(message.from_user.id))
    procedures = procedure_repo.get_active()

    if not procedures:
        await state.set_state(ProcedureStates.waiting_for_id)
        await message.answer(
            "Активных процедур нет.",
            reply_markup=procedures_menu_keyboard(),
        )
        return

    procedures.sort(key=lambda p: p["id"])

    text = "Активные процедуры:\n\n"
    text += "\n".join(
        f"🔹 `{p['id']}`: *{p['name']}*"
        + (f" (_{p['description']}_)" if p.get("description") else "")
        for p in procedures
    )
    text += "\n\n👉 Введите `id` процедуры:"

    await state.set_state(ProcedureStates.waiting_for_id)
    await message.answer(
        text,
        reply_markup=procedures_menu_keyboard(),
        parse_mode='Markdown'
    )


@router.message(
        ProcedureStates.waiting_for_id,
        ~F.text.startswith("/")
        )
async def procedure_open(message: Message, state: FSMContext):
    try:
        procedure_id = int(message.text)
    except ValueError:
        await message.answer(
            "`id` должен быть числом.\n\n👉 Попробуйте снова:",
            reply_markup=procedures_menu_keyboard(),
            parse_mode='Markdown'
        )
        return

    procedure_repo = Procedure(user=str(message.from_user.id))
    procedure = procedure_repo.get_by_id(procedure_id)

    if not procedure or not procedure["active"]:
        await message.answer(
            "Процедура не найдена.\n\n👉 Попробуйте снова:",
            reply_markup=procedures_menu_keyboard(),
            )
        return

    await state.set_state(ProcedureStates.action_select)
    await state.update_data(procedure_id=procedure_id)
    await message.answer(
        "Выбрана процедура:\n\n"
        + format_procedure(procedure),
        reply_markup=procedure_actions_keyboard(),
        parse_mode='Markdown'
    )


@router.message(ProcedureStates.action_select, F.text == "✏️ Изменить описание")
async def procedure_edit_description_start(message: Message, state: FSMContext):
    await state.set_state(ProcedureStates.waiting_for_description)
    await message.answer(
        "Введите описание процедуры:",
        reply_markup=procedure_cancel_keyboard(),
    )


@router.message(
        ProcedureStates.waiting_for_description,
        ~F.text.startswith("/")
        )
async def procedure_edit_description_finish(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.set_state(ProcedureStates.action_select)
        await message.answer(
            "Действие отменено.",
            reply_markup=procedure_actions_keyboard(),
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
        "Процедура обновлена:\n\n"
        + format_procedure(procedure),
        reply_markup=procedure_actions_keyboard(),
        parse_mode='Markdown'
    )


@router.message(ProcedureStates.action_select, F.text == "⛔ Деактивировать")
async def procedure_deactivate_confirm(message: Message, state: FSMContext):
    data = await state.get_data()
    procedure_id = data.get("procedure_id")

    procedure_repo = Procedure(user=str(message.from_user.id))
    procedure = procedure_repo.get_by_id(procedure_id)

    await state.set_state(ProcedureStates.deactivate_confirm)
    await message.answer(
        "Вы уверены, что хотите деактивировать эту процедуру?\n\n"
        + format_procedure(procedure)
        + "\n\n👉 Введите `id` еще раз для подтверждения:",
        reply_markup=procedure_cancel_keyboard(),
        parse_mode='Markdown'
    )


@router.message(
        ProcedureStates.deactivate_confirm,
        ~F.text.startswith("/")
        )
async def procedure_deactivate_process(message: Message, state: FSMContext):
    data = await state.get_data()
    procedure_id = data["procedure_id"]

    if message.text == "❌ Отмена" or message.text != str(procedure_id):
        await state.set_state(ProcedureStates.action_select)
        await message.answer(
            "Деактивация отменена.",
            reply_markup=procedure_actions_keyboard(),
            )
        return

    procedure_repo = Procedure(user=str(message.from_user.id))
    procedure_repo.update_active(procedure_id, False)
    procedures = procedure_repo.get_active()

    if not procedures:
        await state.set_state(ProcedureStates.waiting_for_id)
        await message.answer(
            "Активных процедур нет.",
            reply_markup=procedures_menu_keyboard(),
        )
        return

    text = "Активные процедуры:\n\n"
    text += "────────────────\n"
    text += "\n".join(
        f"🔹 `{p['id']}`: *{p['name']}*"
        + (f" (_{p['description']}_)" if p.get("description") else "")
        for p in procedures
    )
    text += "\n\n👉 Введите `id` процедуры:"

    await state.set_state(ProcedureStates.waiting_for_id)
    await message.answer(
        text,
        reply_markup=procedures_menu_keyboard(),
        parse_mode='Markdown'
    )
