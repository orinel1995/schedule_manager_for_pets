from typing import Optional


def parse_int(value: str) -> Optional[int]:
    """
    Пытается преобразовать строку в int.
    Возвращает None при ошибке.
    """
    try:
        return int(value.strip())
    except (ValueError, AttributeError):
        return None


def split_name_and_type(text: str) -> Optional[tuple[str, str]]:
    """
    Ожидает строку вида: "Имя, Тип"

    Возвращает (name, type) или None при ошибке.
    """
    if not text:
        return None

    parts = [p.strip() for p in text.split(",") if p.strip()]

    if len(parts) < 2:
        return None

    # Берём только первые два элемента
    name, pet_type = parts[0], parts[1]

    if not name or not pet_type:
        return None

    return name, pet_type
