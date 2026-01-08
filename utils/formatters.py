from typing import Dict, List
from datetime import datetime
from core.dates import MONTHS_RU, WEEKDAYS_RU


def active_to_text(active: bool) -> str:
    """
    Преобразует статус активности в человекочитаемый текст.
    """
    return "Активен" if active else "Неактивен"


def format_pet(pet: Dict) -> str:
    """
    Форматирует данные питомца для вывода пользователю.
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


def format_procedure(procedure: Dict) -> str:
    """
    Форматирует данные процедур для вывода пользователю.
    """
    return (
        f"Процедура {procedure['name']}:\n"
        f"Описание: {procedure['description']}\n"
        f"Статус: {active_to_text(procedure['active'])}\n"
        f"id: {procedure['id']}"
    )


def _format_year_date(value: str) -> str:
    """
    value: 'MM-DD'
    """
    date = datetime.strptime(value, "%m-%d")
    return f"{date.day} {MONTHS_RU[date.month]}"


def _format_full_date(value: str) -> str:
    date = datetime.strptime(value, "%Y-%m-%d")
    return f"{date.day} {MONTHS_RU[date.month]} {date.year}"


def pluralize_days(value: int) -> str:
    if 11 <= value % 100 <= 14:
        return "дней"

    last = value % 10
    if last == 1:
        return "день"
    if 2 <= last <= 4:
        return "дня"
    return "дней"


def every_word_for_days(value: int) -> str:
    return "каждый" if pluralize_days(value) == "день" else "каждые"


def format_weekdays(value: str) -> str:
    days = value.split(",")
    return ", ".join(WEEKDAYS_RU.get(day, day) for day in days)


def format_schedule_period(schedule: dict) -> str:
    schedule_type = schedule["schedule_type_id"]
    value = schedule["value"]

    if schedule_type == 1:
        days = int(value)
        return f"{every_word_for_days(days)} {days} {pluralize_days(days)}"

    if schedule_type == 2:
        return f"{format_weekdays(value)}"

    if schedule_type == 3:
        return f"каждое {value} число месяца"

    if schedule_type == 4:
        return f"каждый год {_format_year_date(value)}"

    if schedule_type == 5:
        return f"единоразово {_format_full_date(value)}"

    return "неизвестная периодичность"


def format_schedule(schedule: dict) -> str:
    return (
        f"Питомец: {schedule['pet_name']}\n"
        f"Процедура: {schedule['procedure_name']}\n"
        f"Периодичность: {format_schedule_period(schedule)}\n"
        f"Статус: {active_to_text(schedule['active'])}\n"
        f"id: {schedule['id']}"
    )


def format_schedules_grouped(schedules: list[dict]) -> str:
    if not schedules:
        return "Активных расписаний нет."

    grouped: dict[str, list[dict]] = {}

    for schedule in schedules:
        pet_name = schedule["pet_name"]
        grouped.setdefault(pet_name, []).append(schedule)

    lines: list[str] = []

    for pet_name, pet_schedules in grouped.items():
        lines.append(f"Питомец {pet_name}:")

        for s in pet_schedules:
            lines.append(
                f"  {s['id']}: {s['procedure_name']} - "
                f"{format_schedule_period(s)}"
            )

        lines.append("")  # пустая строка между питомцами

    return "\n".join(lines).strip()
