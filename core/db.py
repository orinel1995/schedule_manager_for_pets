"""
Модуль работы с базой данных.

Содержит универсальный контекстный менеджер для подключения
к SQLite с автоматическим управлением транзакциями.
"""

import sqlite3
from contextlib import contextmanager
from typing import Iterator


@contextmanager
def db_connection(db_name: str) -> Iterator[sqlite3.Connection]:
    """
    Контекстный менеджер для работы с SQLite-соединением.

    Гарантирует:
    - commit при успешном выполнении блока
    - rollback при исключении
    - корректное закрытие соединения

    :param db_name: имя файла базы данных SQLite
    :yield: sqlite3.Connection
    """
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
