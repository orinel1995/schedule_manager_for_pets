"""
Модуль доступа к данным таблицы pet.

Содержит класс Pet, предоставляющий CRUD-операции для работы с питомцами.
"""

from typing import Optional, Dict, List
from datetime import date

from core.db import db_connection, DB_NAME, USER_NAME
from core.logger import get_logger
from core.dates import parse_user_date

logger = get_logger()


class Pet:
    """
    Методы для работы с таблицей pet.
    """

    def __init__(self, db_name: str = DB_NAME, user: str = USER_NAME):
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
    ) -> Optional[int]:
        """
        Создаёт нового питомца и возвращает id.

        Если активный питомец с таким именем уже существует,
        новая запись не создаётся. В этом случае возвращается id существующей
        записи.
        :param name: имя питомца
        :param pet_type: тип питомца
        :param start_date: дата добавления/появления/рождения питомца
        """
        start_date = parse_user_date(start_date) or date.today().isoformat()

        with db_connection(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id
                FROM pet
                WHERE name = ? AND active = 1
                LIMIT 1
            """, (name,))

            existing = cursor.fetchone()

            if existing is not None:
                pet_id = existing["id"]

                logger.error(
                    (
                        f"Попытка создать питомца с существующим "
                        f"name='{name}'. Возвращён существующий id={pet_id}"
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
        """
        Обновляет имя питомца.

        :param pet_id: id питомца
        :param name: имя питомца
        """
        self._simple_update(pet_id, "name", name)

    def update_type(self, pet_id: int, pet_type: str) -> None:
        """
        Обновляет тип питомца.

        :param pet_id: id питомца
        :param pet_type: тип питомца
        """
        self._simple_update(pet_id, "type", pet_type)

    def update_start_date(
            self,
            pet_id: int,
            start_date: Optional[str]
            ) -> None:
        """
        Обновляет дату появления/рождения питомца.

        :param pet_id: id питомца
        :param start_date: дата в формате "DD.MM.YYYY" или "YYYY-MM-DD"
        """
        start_date = parse_user_date(start_date)

        if start_date is None:
            start_date = date.today().isoformat()

        self._simple_update(pet_id, "start_date", start_date)

    def update_active(self, pet_id: int, active: bool) -> None:
        """
        Обновляет статус активности питомца.

        Если новое значение совпадает с текущим —
        операция не выполняется.

        :param pet_id: id питомца
        :param active: статус активности
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
                    f"Попытка изменить active у несуществующего питомца "
                    f"id={pet_id}",
                    extra={"user": self.user}
                )
                return

            current_active = bool(row["active"])

            if current_active == active:
                logger.info(
                    f"Питомец id={pet_id}: active уже равен {active}, "
                    f"изменений не требуется",
                    extra={"user": self.user}
                )
                return

            cursor.execute("""
                UPDATE pet
                SET active = ?
                WHERE id = ?
            """, (int(active), pet_id))

            logger.info(
                f"Питомец id={pet_id}: active изменён на {active}",
                extra={"user": self.user}
            )

    def get_by_id(self, pet_id: int) -> Optional[Dict]:
        """
        Возвращает данные о питомце по id в виде словаря.

        :param pet_id: id питомца
        """
        with db_connection(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, name, type, start_date, active
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
        """
        Удаляет питомца по id.

        :param pet_id: id питомца
        """
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

        :param pet_id: id питомца
        :param field: поле для изменения
        :param value: новое значение
        """
        with db_connection(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute(
                f"UPDATE pet SET {field} = ? WHERE id = ?",
                (value, pet_id)
            )

        logger.info(
            f"Питомец id={pet_id}: обновлено поле {field}, значение '{value}'",
            extra={"user": self.user}
        )
