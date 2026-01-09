from datetime import date
from typing import List, Dict

from core.db import db_connection, DB_NAME, USER_NAME
from data_access.schedule import Schedule


class Checklist:
    def __init__(self, db_name: str = DB_NAME, user: str = USER_NAME):
        """
        :param db_name: имя файла базы данных SQLite
        :param user: пользователь, от имени которого выполняются операции
        """
        self.db_name = db_name
        self.user = user

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
                        schedule_id,
                        status,
                        active
                    )
                    VALUES (?, ?, ?, ?, 0, 1)
                """, (
                    today,
                    item["pet_id"],
                    item["procedure_id"],
                    item["schedule_id"],
                ))

            conn.commit()

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
                    sh.end_date AS end_date,
                    pr.description AS procedure_description
                FROM checklist c
                JOIN pet p ON p.id = c.pet_id
                JOIN procedure pr ON pr.id = c.procedure_id
                JOIN schedule sh ON sh.id = c.schedule_id
                WHERE c.date = ?
                    AND c.active = 1
                    AND (
                        sh.end_date >= ?
                        OR sh.end_date is NULL
                    )
                ORDER BY p.name, pr.name
            """, (today, today))

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

    def update_inactive(self, user: str = USER_NAME) -> None:
        """
        Находит задания, которых нет в текущем расписании и отключает их.
        """
        today = date.today()
        schedule_repo = Schedule(user=user)
        active_schedules: List[Dict] = schedule_repo.get_active()

        active_pairs = set()

        for s in active_schedules:
            start_date = (
                date.fromisoformat(s["start_date"])
                if s["start_date"] is not None
                else None
            )
            end_date = (
                date.fromisoformat(s["end_date"])
                if s["end_date"] is not None
                else None
            )

            if (
                (start_date is None or start_date <= today)
                and (end_date is None or today <= end_date)
            ):
                active_pairs.add((s["pet_id"], s["procedure_id"]))

        with db_connection(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, pet_id, procedure_id, date
                FROM checklist
                WHERE date = ? AND active = 1
            """, (today,)
            )

            checklist_rows = cursor.fetchall()

            for row in checklist_rows:
                pair = (row["pet_id"], row["procedure_id"])
                if pair not in active_pairs:
                    # проверяем, есть ли уже запись с active=0
                    cursor.execute("""
                        SELECT 1
                        FROM checklist
                        WHERE date = ?
                            AND pet_id = ?
                            AND procedure_id = ?
                            AND active = 0
                    """, (row["date"], row["pet_id"], row["procedure_id"]))

                    if cursor.fetchone() is None:
                        cursor.execute("""
                            UPDATE checklist
                            SET active = 0
                            WHERE id = ?
                        """, (row["id"],))

            conn.commit()
