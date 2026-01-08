from datetime import date
from typing import List, Dict

from core.db import db_connection, DB_NAME, USER_NAME


class Checklist:
    def __init__(self, db_name: str = DB_NAME, user: str = USER_NAME):
        """
        :param db_name: имя файла базы данных SQLite
        :param user: пользователь, от имени которого выполняются операции
        """
        self.db_name = db_name
        self.user = user

    # ---------- ИНИЦИАЛИЗАЦИЯ ЗАДАНИЙ НА СЕГОДНЯ ----------

    def ensure_today_tasks(self, schedules: List[Dict]) -> None:
        """
        Создаёт записи чеклиста на сегодня на основе расписаний.
        Если запись уже существует (date + pet_id + procedure_id),
        она не изменяется.

        :param schedules: результат Schedule.get_today()
        """
        today = date.today().isoformat()

        with db_connection(self.db_name) as conn:
            cursor = conn.cursor()

            for item in schedules:
                cursor.execute("""
                    INSERT OR IGNORE INTO checklist (
                        date,
                        pet_id,
                        procedure_id,
                        status
                    )
                    VALUES (?, ?, ?, 0)
                """, (
                    today,
                    item["pet_id"],
                    item["procedure_id"],
                ))

            conn.commit()

    # ---------- ПОЛУЧЕНИЕ ЧЕКЛИСТА НА СЕГОДНЯ ----------

    def get_today(self) -> List[Dict]:
        """
        Возвращает чеклист на сегодня со статусами выполнения.
        """
        today = date.today().isoformat()

        with db_connection(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    c.id,
                    c.status,
                    p.name AS pet_name,
                    pr.name AS procedure_name,
                    pr.description AS procedure_description
                FROM checklist c
                JOIN pet p ON p.id = c.pet_id
                JOIN procedure pr ON pr.id = c.procedure_id
                WHERE c.date = ?
                ORDER BY p.name, pr.name
            """, (today,))

            rows = cursor.fetchall()

        return [
            {
                "id": row["id"],
                "status": bool(row["status"]),
                "pet_name": row["pet_name"],
                "procedure_name": row["procedure_name"],
                "procedure_description": row["procedure_description"],
            }
            for row in rows
        ]

    # ---------- ОБНОВЛЕНИЕ СТАТУСА ----------

    def set_status(self, checklist_id: int, status: bool) -> None:
        """
        Обновляет статус выполнения задачи.
        """
        with db_connection(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE checklist
                SET status = ?
                WHERE id = ?
            """, (
                int(status),
                checklist_id,
            ))

            conn.commit()
