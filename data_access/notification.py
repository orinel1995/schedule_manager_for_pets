from typing import Optional

from core.db import db_connection, DB_NAME, USER_NAME


class Notification:
    def __init__(self, db_name: str = DB_NAME, user: str = USER_NAME):
        """
        :param db_name: имя файла базы данных SQLite
        :param user: пользователь, от имени которого выполняются операции
        """
        self.db_name = db_name
        self.user = user

    def set_new_notification(self, value: Optional[str]) -> None:
        """
        Создаёт или обновляет расписание уведомлений пользователя.

        :param user_id: Telegram user_id
        :param value: время в формате HH:MM или None для отключения
        """
        with db_connection(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO notification (user_id, value)
                VALUES (?, ?)
                ON CONFLICT(user_id)
                DO UPDATE SET value = excluded.value
            """, (
                self.user,
                value,
            ))

            conn.commit()

    def get_user_notification(self) -> Optional[str]:
        """
        Возвращает текущее расписание уведомлений пользователя.

        :param user_id: Telegram user_id
        :return: строка времени HH:MM или None
        """
        with db_connection(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT value
                FROM notification
                WHERE user_id = ?
            """, (self.user,))

            row = cursor.fetchone()

        if row is None:
            return None

        return row["value"]

    def get_all_active(self) -> list[dict]:
        """
        Возвращает список всех активных напоминаний
        """
        with db_connection(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT user_id, value
                FROM notification
                WHERE value IS NOT NULL
            """)

            rows = cursor.fetchall()

        return [
            {
                "user_id": row["user_id"],
                "value": row["value"],
            }
            for row in rows
        ]
