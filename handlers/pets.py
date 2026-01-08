from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from data_access.pet import Pet
from states.pets import PetsStates
from keyboards.pets import (
    pets_menu_keyboard,
    pet_actions_keyboard,
    pet_deactivate_keyboard,
)
from core.dates import parse_user_date
from utils.formatters import format_pet

router = Router()
CONTEXT_ERROR_TEXT = "Контекст действия утерян. Начните заново."

# ---------- /pets ----------


@router.message(F.text == "/pets")
async def pets_menu(message: Message, state: FSMContext):
    await state.set_state(PetsStates.action_select)
    await message.answer(
        "Выберите действие:",
        reply_markup=pets_menu_keyboard()
    )


# ---------- СОЗДАНИЕ ПИТОМЦА ----------

@router.message(F.text == "➕ Создать нового питомца")
async def pet_create_start(message: Message, state: FSMContext):
    await state.set_state(PetsStates.create_waiting_input)
    await message.answer(
        "Введите имя и тип питомца через запятую, пример:\nБарсик, кот",
        reply_markup=pet_deactivate_keyboard()
    )


@router.message(PetsStates.create_waiting_input)
async def pet_create_process(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "Действие отменено.",
            reply_markup=pets_menu_keyboard()
            )
        return

    parts = [p.strip() for p in message.text.split(",")][:2]
    if len(parts) < 2 or not all(parts):
        await message.answer(
            "Не удалось создать питомца из введенных данных, попробуйте заново:"
        )
        return

    name, pet_type = parts

    pet_repo = Pet(user=str(message.from_user.id))
    pet_id = pet_repo.create(name, pet_type)
    pet = pet_repo.get_by_id(pet_id)

    await state.update_data(pet_id=pet_id)
    await state.set_state(PetsStates.action_select)
    await message.answer(
        "Получен питомец:" + "\n\n" + format_pet(pet),
        reply_markup=pet_actions_keyboard(),
        parse_mode='Markdown'
    )


# ---------- ВЫБОР ПИТОМЦА ----------

@router.message(F.text == "📋 Выбрать существующего")
async def pet_select_start(message: Message, state: FSMContext):
    pet_repo = Pet(user=str(message.from_user.id))
    pets = pet_repo.get_active()

    pets.sort(key=lambda x: x["id"])

    if not pets:
        await message.answer(
            "Активных питомцев нет.",
            reply_markup=pets_menu_keyboard()
            )
        return

    text = "Выберите питомца:\n\n"
    text += "\n".join(f"🔹 `{p['id']}`: *{p['name']}* (_{p['type']}_)" for p in pets)
    text += "\n\n👉 Введите id:"

    await state.set_state(PetsStates.select_waiting_id)
    await message.answer(
        text, 
        reply_markup=pet_deactivate_keyboard(),
        parse_mode='Markdown')


@router.message(PetsStates.select_waiting_id)
async def pet_select_process(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "Действие отменено.",
            reply_markup=pets_menu_keyboard()
            )
        return

    if not message.text.isdigit():
        await message.answer("id не найден, попробуйте заново:")
        return

    pet_id = int(message.text)
    pet_repo = Pet(user=str(message.from_user.id))
    pet = pet_repo.get_by_id(pet_id)

    if pet is None or not pet["active"]:
        await message.answer("id не найден, попробуйте заново:")
        return

    await state.update_data(pet_id=pet_id)
    await state.set_state(PetsStates.action_select)
    await message.answer(
        f"Действия для {pet['type']} {pet['name']}:",
        reply_markup=pet_actions_keyboard()
    )


# ---------- ДЕЙСТВИЯ ----------

@router.message(PetsStates.action_select, F.text == "✏️ Изменить имя")
async def pet_rename_start(message: Message, state: FSMContext):
    await state.set_state(PetsStates.rename_waiting)
    await message.answer("Укажите новое имя:")


@router.message(PetsStates.rename_waiting)
async def pet_rename_process(message: Message, state: FSMContext):
    data = await state.get_data()
    pet_id = data.get("pet_id")

    pet_repo = Pet(user=str(message.from_user.id))
    pet_repo.update_name(pet_id, message.text)

    pet = pet_repo.get_by_id(pet_id)
    await state.set_state(PetsStates.action_select)
    await message.answer(
        "Данные изменены:\n\n" + format_pet(pet),
        reply_markup=pet_actions_keyboard(),
        parse_mode='Markdown'
    )


@router.message(PetsStates.action_select, F.text == "✏️ Изменить тип")
async def pet_change_type_start(message: Message, state: FSMContext):
    await state.set_state(PetsStates.type_waiting)
    await message.answer("Укажите новый тип:")


@router.message(PetsStates.type_waiting)
async def pet_change_type_process(message: Message, state: FSMContext):
    data = await state.get_data()
    pet_id = data.get("pet_id")

    pet_repo = Pet(user=str(message.from_user.id))
    pet_repo.update_type(pet_id, message.text)

    pet = pet_repo.get_by_id(pet_id)
    await state.set_state(PetsStates.action_select)
    await message.answer(
        "Данные изменены:\n\n" + format_pet(pet),
        reply_markup=pet_actions_keyboard(),
        parse_mode='Markdown'
    )


@router.message(PetsStates.action_select, F.text == "📅 Изменить дату рождения")
async def pet_change_date_start(message: Message, state: FSMContext):
    await state.set_state(PetsStates.date_waiting)
    await message.answer("Укажите новую дату в формате DD.MM.YYYY:")


@router.message(PetsStates.date_waiting)
async def pet_change_date_process(message: Message, state: FSMContext):
    parsed = parse_user_date(message.text)
    if parsed is None:
        await message.answer("Не верный формат даты, попробуйте заново:")
        return

    data = await state.get_data()
    pet_id = data.get("pet_id")

    pet_repo = Pet(user=str(message.from_user.id))
    pet_repo.update_start_date(pet_id, parsed)

    pet = pet_repo.get_by_id(pet_id)
    await state.set_state(PetsStates.action_select)
    await message.answer(
        "Данные изменены:\n\n" + format_pet(pet),
        reply_markup=pet_actions_keyboard(),
        parse_mode='Markdown'
    )


# ---------- ДЕАКТИВАЦИЯ ----------

@router.message(PetsStates.action_select, F.text == "⛔ Деактивировать")
async def pet_deactivate_confirm(message: Message, state: FSMContext):
    data = await state.get_data()
    pet_id = data.get("pet_id")

    pet_repo = Pet(user=str(message.from_user.id))
    pet = pet_repo.get_by_id(pet_id)

    await state.set_state(PetsStates.deactivate_confirm)

    await message.answer(
        "Вы уверены, что хотите деактивировать этого питомца?\n\n"
        + format_pet(pet)
        + "\n\n👉 Введите id еще раз:",
        reply_markup=pet_deactivate_keyboard(),
        parse_mode='Markdown'
    )


@router.message(PetsStates.deactivate_confirm)
async def pet_deactivate_process(message: Message, state: FSMContext):
    data = await state.get_data()
    pet_id = data.get("pet_id")

    if message.text == "❌ Отмена" or message.text != str(pet_id):
        await state.set_state(PetsStates.action_select)
        await message.answer(
            "Деактивация отменена.",
            reply_markup=pet_actions_keyboard(),
            )
        return

    pet_repo = Pet(user=str(message.from_user.id))
    pet_repo.update_active(pet_id, False)

    await state.set_state(PetsStates.action_select)
    await message.answer(
        "Питомец деактивирован.",
        reply_markup=pets_menu_keyboard(),
        parse_mode='Markdown'
    )
