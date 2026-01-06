"""
Модуль доступа к данным таблицы procedure.

Содержит класс Procedure, предоставляющий операции создания,
удаления и обновления процедур.

Все операции логируются в общий CSV-лог проекта.
"""

from typing import Optional, Dict, List

from core.logger import get_logger
from core.db import db_connection


logger = get_logger()


class Procedure:
    """
    Репозиторий для работы с таблицей procedure.
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
        description: Optional[str] = None
    ) -> int:
        """
        Создаёт новую процедуру.

        Если процедура с таким именем уже существует,
        новая запись не создаётся. Возвращается id существующей записи
        и логируется ошибка.

        :param name: название процедуры (обязательно)
        :param description: описание процедуры (опционально)
        :return: id созданной или существующей процедуры
        """
        with db_connection(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id
                FROM procedure
                WHERE name = ?
                LIMIT 1
            """, (name,))

            existing = cursor.fetchone()

            if existing is not None:
                procedure_id = existing["id"]

                logger.error(
                    (
                        f"Попытка создать процедуру с существующим name='{name}'. "
                        f"Возвращён существующий id={procedure_id}"
                    ),
                    extra={"user": self.user}
                )
                return procedure_id

            cursor.execute("""
                INSERT INTO procedure (name, description, active)
                VALUES (?, ?, 1)
            """, (name, description))

            procedure_id = cursor.lastrowid

        logger.info(
            (
                f"Создана процедура id={procedure_id}, "
                f"name='{name}', description='{description}'"
            ),
            extra={"user": self.user}
        )

        return procedure_id

    def update_active(self, procedure_id: int, active: bool) -> None:
        """
        Обновляет статус активности процедуры.
        """
        with db_connection(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE procedure
                SET active = ?
                WHERE id = ?
            """, (int(active), procedure_id))

        logger.info(
            f"Процедура id={procedure_id}: active={active}",
            extra={"user": self.user}
        )

    def update_description(
        self,
        procedure_id: int,
        description: Optional[str]
    ) -> None:
        """
        Обновляет описание процедуры.
        """
        with db_connection(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE procedure
                SET description = ?
                WHERE id = ?
            """, (description, procedure_id))

        logger.info(
            f"Процедура id={procedure_id}: обновлено description",
            extra={"user": self.user}
        )

    def delete(self, procedure_id: int) -> None:
        """
        Удаляет процедуру по id.
        """
        with db_connection(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM procedure WHERE id = ?",
                (procedure_id,)
            )

        logger.info(
            f"Процедура id={procedure_id} удалена",
            extra={"user": self.user}
        )

    def get_by_id(self, procedure_id: int) -> Optional[Dict]:
        """
        Возвращает процедуру по id в виде словаря.

        :param procedure_id: идентификатор процедуры
        :return: словарь с данными процедуры или None
        """
        with db_connection(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, name, description, active
                FROM procedure
                WHERE id = ?
            """, (procedure_id,))

            row = cursor.fetchone()

        if row is None:
            return None

        return {
            "id": row["id"],
            "name": row["name"],
            "description": row["description"],
            "active": bool(row["active"])
        }

    def get_active(self) -> List[Dict]:
        """
        Возвращает список всех активных процедур.

        :return: список словарей с активными процедурами
        """
        with db_connection(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, name, description, active
                FROM procedure
                WHERE active = 1
                ORDER BY id
            """)

            rows = cursor.fetchall()

        result: List[Dict] = []

        for row in rows:
            result.append({
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "active": True
            })

        return result
