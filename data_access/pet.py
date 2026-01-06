"""
Модуль доступа к данным таблицы pet.

Содержит класс Pet, предоставляющий CRUD-операции для работы с питомцами,
а также вспомогательные функции для валидации и парсинга дат.

Все операции логируются в общий CSV-лог проекта.
"""

from datetime import date, datetime
from typing import Optional, Dict, List

from core.db import db_connection
from core.logger import get_logger


logger = get_logger()


def parse_date(value: Optional[str]) -> Optional[str]:
    """
    Преобразует строковое представление даты в формат YYYY-MM-DD.

    Поддерживаемые форматы:
    - YYYY-MM-DD
    - DD.MM.YYYY

    :param value: строка с датой или None
    :return: дата в формате YYYY-MM-DD или None
    :raises ValueError: если формат даты некорректный
    """
    if value is None:
        return None

    try:
        return datetime.strptime(value, "%Y-%m-%d").date().isoformat()
    except ValueError:
        try:
            return datetime.strptime(value, "%d.%m.%Y").date().isoformat()
        except ValueError:
            raise ValueError(f"Неверный формат даты: {value}")


class Pet:
    """
    Репозиторий для работы с таблицей pet.
    """

    def __init__(self, db_name: str = "project.db", user: str = "admin"):
        """
        :param db_name: имя файла базы данных SQLite
        :param user: пользователь, от имени которого выполняются операции
        """
        self.db_name = db_name
        self.user = user

    def create(
        self,
        name: str,
        pet_type: str,
        start_date: Optional[str] = None
    ) -> int:
        """
        Создаёт нового питомца.

        Если питомец с таким именем уже существует, новая запись не создаётся.
        В этом случае возвращается id существующей записи и логируется ошибка.
        """
        start_date = parse_date(start_date) or date.today().isoformat()

        with db_connection(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id
                FROM pet
                WHERE name = ?
                LIMIT 1
            """, (name,))

            existing = cursor.fetchone()

            if existing is not None:
                pet_id = existing["id"]

                logger.error(
                    (
                        f"Попытка создать питомца с существующим name='{name}'. "
                        f"Возвращён существующий id={pet_id}"
                    ),
                    extra={"user": self.user}
                )
                return pet_id

            cursor.execute("""
                INSERT INTO pet (name, type, start_date, active)
                VALUES (?, ?, ?, 1)
            """, (name, pet_type, start_date))

            pet_id = cursor.lastrowid

        logger.info(
            (
                f"Создан питомец id={pet_id}, name='{name}', "
                f"type='{pet_type}', start_date='{start_date}'"
            ),
            extra={"user": self.user}
        )

        return pet_id

    def update_name(self, pet_id: int, name: str) -> None:
        """Обновляет имя питомца."""
        self._simple_update(pet_id, "name", name)

    def update_type(self, pet_id: int, pet_type: str) -> None:
        """Обновляет тип питомца."""
        self._simple_update(pet_id, "type", pet_type)

    def update_start_date(self, pet_id: int, start_date: str) -> None:
        """Обновляет дату начала."""
        start_date = parse_date(start_date)
        self._simple_update(pet_id, "start_date", start_date)

    def update_active(self, pet_id: int, active: bool) -> None:
        """
        Универсально обновляет статус активности питомца.

        Переходы:
        - False -> True: active = 1, end_date = NULL
        - True -> False: active = 0, end_date = today
        - Без изменения состояния — операция не выполняется
        """
        with db_connection(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT active
                FROM pet
                WHERE id = ?
            """, (pet_id,))

            row = cursor.fetchone()

            if row is None:
                logger.error(
                    f"Попытка изменить active у несуществующего питомца id={pet_id}",
                    extra={"user": self.user}
                )
                return

            current_active = bool(row["active"])

            if current_active == active:
                logger.info(
                    f"Питомец id={pet_id}: active уже равен {active}, изменений не требуется",
                    extra={"user": self.user}
                )
                return

            if current_active and not active:
                end_date = date.today().isoformat()

                cursor.execute("""
                    UPDATE pet
                    SET active = 0, end_date = ?
                    WHERE id = ?
                """, (end_date, pet_id))

                logger.info(
                    f"Питомец id={pet_id}: active=False, end_date={end_date}",
                    extra={"user": self.user}
                )

            elif not current_active and active:
                cursor.execute("""
                    UPDATE pet
                    SET active = 1, end_date = NULL
                    WHERE id = ?
                """, (pet_id,))

                logger.info(
                    f"Питомец id={pet_id}: active=True, end_date очищена",
                    extra={"user": self.user}
                )

    def get_by_id(self, pet_id: int) -> Optional[Dict]:
        """
        Возвращает питомца по id в виде словаря.
        """
        with db_connection(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, name, type, start_date, end_date, active
                FROM pet
                WHERE id = ?
            """, (pet_id,))

            row = cursor.fetchone()

        if row is None:
            return None

        return {
            "id": row["id"],
            "name": row["name"],
            "type": row["type"],
            "start_date": row["start_date"],
            "end_date": row["end_date"],
            "active": bool(row["active"])
        }

    def get_active(self) -> List[Dict]:
        """
        Возвращает список всех активных питомцев.
        """
        with db_connection(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id
                FROM pet
                WHERE active = 1
                ORDER BY id
            """)

            rows = cursor.fetchall()

        result: List[Dict] = []

        for row in rows:
            pet_data = self.get_by_id(row["id"])
            if pet_data is not None:
                result.append(pet_data)

        return result

    def delete(self, pet_id: int) -> None:
        """Удаляет питомца по id."""
        with db_connection(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM pet WHERE id = ?", (pet_id,))

        logger.info(
            f"Питомец id={pet_id} удалён",
            extra={"user": self.user}
        )

    def _simple_update(self, pet_id: int, field: str, value) -> None:
        """
        Внутренний метод для обновления одного поля записи.
        """
        with db_connection(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute(
                f"UPDATE pet SET {field} = ? WHERE id = ?",
                (value, pet_id)
            )

        logger.info(
            f"Питомец id={pet_id}: обновлено поле {field}",
            extra={"user": self.user}
        )
