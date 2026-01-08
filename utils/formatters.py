from typing import Dict, List


def active_to_text(active: bool) -> str:
    """
    Преобразует статус активности в человекочитаемый текст.
    """
    return "Активен" if active else "Неактивен"


def format_pet(pet: Dict) -> str:
    """
    Форматирует данные питомца для вывода пользователю.

    Ожидаемый формат pet:
    {
        "id": int,
        "name": str,
        "type": str,
        "start_date": str,
        "active": bool
    }
    """
    return (
        f"Питомец {pet['name']}:\n"
        f"Тип: {pet['type']}\n"
        f"День рождения: {pet['start_date']}\n"
        f"Статус: {active_to_text(pet['active'])}\n"
        f"id: {pet['id']}"
    )


def format_pet_created(pet: Dict) -> str:
    """
    Сообщение после создания питомца.
    """
    return (
        f"Получен питомец {pet['id']}: "
        f"{pet['name']} {pet['type']}, "
        f"статус {active_to_text(pet['active'])}"
    )


def format_pet_list(pets: List[Dict]) -> str:
    """
    Форматирует список питомцев вида:
    id: name
    """
    if not pets:
        return "Активных питомцев нет."

    lines = []
    pets_sorted = sorted(pets, key=lambda x: x['id'])
    for pet in pets_sorted:
        lines.append(f"{pet['id']}: {pet['name']}")

    return "Активные питомцы:\n\n" + "\n".join(lines)
