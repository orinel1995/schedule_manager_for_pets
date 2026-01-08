from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def today_checklist_keyboard(items: list[dict]) -> InlineKeyboardMarkup:
    keyboard = []

    for item in items:
        status_icon = "✅" if item["status"] else "⬜"
        text = (
            f"{status_icon} "
            f"{item['pet_name']}: "
            f"{item['procedure_name']}"
        )

        if item.get("procedure_description"):
            text += f" ({item['procedure_description']})"

        keyboard.append([
            InlineKeyboardButton(
                text=text,
                callback_data=f"checklist_toggle:{item['id']}"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
