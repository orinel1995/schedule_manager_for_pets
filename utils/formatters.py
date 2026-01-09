from typing import Dict
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
        f"🐾 *{pet['name']}* _({pet['type']})_\n"
        f"────────────────────\n"
        f"День рождения: {_format_full_date(pet['start_date'])}\n"
        f"Статус: {active_to_text(pet['active'])}\n"
        f"id: `{pet['id']}`"
    )


def format_procedure(procedure: Dict) -> str:
    """
    Форматирует данные процедур для вывода пользователю.
    """
    description = procedure['description'] or "Нет описания"

    return (
        f"🧪 *{procedure['name']}*\n"
        f"────────────────────\n"
        f"Описание: {description}\n"
        f"Статус: {active_to_text(procedure['active'])}\n"
        f"id: `{procedure['id']}`"
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
        return f"{_format_full_date(value)}"

    return "неизвестная периодичность"


def format_schedule(schedule: dict) -> str:
    procedure_description = schedule.get('procedure_description')
    if procedure_description:
        description = f"(_{procedure_description}_)"
    else:
        description = ""

    return (
        f"🐾 *{schedule['pet_name']}*\n"
        f"🧪 *{schedule['procedure_name']}* {description}\n"
        f"────────────────────\n"
        f"Периодичность: {format_schedule_period(schedule)}\n"
        f"Дата начала: {_format_full_date(schedule['start_date'])}\n"
        f"Статус: {active_to_text(schedule['active'])}\n"
        f"id: {schedule['id']}"
    )


def format_schedules_grouped(schedules: list[dict]) -> str:
    grouped: dict[str, list[dict]] = {}

    for schedule in schedules:
        pet_name = schedule["pet_name"]
        grouped.setdefault(pet_name, []).append(schedule)

    lines: list[str] = []

    for pet_name, pet_schedules in grouped.items():
        pet_type = pet_schedules[0].get("pet_type", "???")

        lines.append(f"🐾 *{pet_name}* _({pet_type})_")
        lines.append("────────────────────")

        for s in pet_schedules:
            lines.append(
                f"🔹 `{s['id']}`: "
                f"{s['procedure_name']} — _{format_schedule_period(s)}_"
            )

        lines.append("")  # пустая строка между питомцами

    return "\n".join(lines).strip()
