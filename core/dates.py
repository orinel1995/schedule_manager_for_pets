"""
Модуль для работы с пользовательскими датами и календарной логикой.

Используется во всех частях проекта для:
- парсинга пользовательского ввода дат
- нормализации форматов
- вспомогательных календарных вычислений
"""

from datetime import date, datetime
from typing import Optional, List, Any
from enum import Enum


SUPPORTED_DATE_FORMATS = (
    "%Y-%m-%d",   # 2025-12-01
    "%d.%m.%Y",   # 01.12.2025
)

MONTHS_RU = {
    1: "января",
    2: "февраля",
    3: "марта",
    4: "апреля",
    5: "мая",
    6: "июня",
    7: "июля",
    8: "августа",
    9: "сентября",
    10: "октября",
    11: "ноября",
    12: "декабря",
}

WEEKDAYS_RU = {
    "MONDAY": "каждый понедельник",
    "TUESDAY": "каждый вторник",
    "WEDNESDAY": "каждую среду",
    "THURSDAY": "каждый четверг",
    "FRIDAY": "каждую пятницу",
    "SATURDAY": "каждую субботу",
    "SUNDAY": "каждое воскресенье",
}


class WeekDay(Enum):
    """Для валидации и нормализации пользовательского ввода."""
    MONDAY = ("пн", "понедельник")
    TUESDAY = ("вт", "вторник")
    WEDNESDAY = ("ср", "среда")
    THURSDAY = ("чт", "четверг")
    FRIDAY = ("пт", "пятница")
    SATURDAY = ("сб", "суббота")
    SUNDAY = ("вс", "воскресенье")

    @classmethod
    def parse(cls, value: str) -> Optional["WeekDay"]:
        normalized = value.strip().lower()

        for day in cls:
            if normalized in day.value:
                return day

        return None

    @classmethod
    def parse_many(cls, value: str) -> list["WeekDay"]:
        result = []
        for part in value.split(","):
            day = cls.parse(part)
            if day is not None:
                result.append(day)

        return result


def parse_user_date(value: Optional[str]) -> Optional[str]:
    """
    Парсит пользовательский ввод даты и возвращает строку в формате YYYY-MM-DD.

    Поддерживаемые форматы:
    - YYYY-MM-DD
    - DD.MM.YYYY

    :param value: строка с датой или None
    :return: строка YYYY-MM-DD или None
    :raises ValueError: если формат даты некорректный
    """
    if value is None:
        return None

    for fmt in SUPPORTED_DATE_FORMATS:
        try:
            return datetime.strptime(value.strip(), fmt).date().isoformat()
        except ValueError:
            continue

    raise ValueError(f"Неверный формат даты: {value}")


def parse_user_date_to_date(value: str) -> date:
    """
    Парсит пользовательский ввод даты и возвращает объект date.

    Используется в местах, где требуется арифметика дат.
    """
    for fmt in SUPPORTED_DATE_FORMATS:
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue

    raise ValueError(f"Неверный формат даты: {value}")


def normalize_yearly_date(value: str) -> str:
    """
    Преобразует пользовательскую дату в формат MM-DD для ежегодных расписаний.

    Примеры:
    - 2025-12-01 -> 12-01
    - 01.12.2025 -> 12-01
    """
    parsed = parse_user_date_to_date(value)
    return parsed.strftime("%m-%d")


def last_day_of_month(d: date) -> int:
    """
    Возвращает последний день месяца для переданной даты.

    Используется для корректной обработки ежемесячных расписаний
    (например, 31 февраля).
    """
    if d.month == 12:
        next_month = date(d.year + 1, 1, 1)
    else:
        next_month = date(d.year, d.month + 1, 1)

    return (next_month - date.resolution).day
