"""
Модуль работы с базой данных.

Содержит:
- контекстный менеджер подключения к SQLite
- инициализацию структуры БД
- заполнение справочников
"""

import os
import sqlite3
from contextlib import contextmanager
from typing import Iterator

from core.logger import get_logger

DB_NAME = "project.db"
USER_NAME = "system"

logger = get_logger()


# ---------- Контекст подключения ----------

@contextmanager
def db_connection(db_name: str = DB_NAME) -> Iterator[sqlite3.Connection]:
    """
    Контекстный менеджер для работы с SQLite.

    - commit при успехе
    - rollback при ошибке
    - гарантированное закрытие соединения
    """
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------- Инициализация БД ----------

def _create_tables(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pet (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        start_date TEXT NOT NULL,
        active INTEGER NOT NULL CHECK (active IN (0, 1))
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS procedure (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        active INTEGER NOT NULL CHECK (active IN (0, 1))
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schedule_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        description TEXT NOT NULL UNIQUE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pet_id INTEGER NOT NULL,
        procedure_id INTEGER NOT NULL,
        schedule_type_id INTEGER NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT,
        value TEXT NOT NULL,
        active INTEGER NOT NULL CHECK (active IN (0, 1)),
        parent_schedule INTEGER DEFAULT NULL,

        FOREIGN KEY (pet_id) REFERENCES pet(id) ON DELETE CASCADE,
        FOREIGN KEY (procedure_id) REFERENCES procedure(id) ON DELETE CASCADE,
        FOREIGN KEY (schedule_type_id) REFERENCES schedule_types(id) ON DELETE CASCADE,
        FOREIGN KEY (parent_schedule) REFERENCES schedule(id) ON DELETE SET NULL
    );
    """)

    cursor.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS uq_schedule_active_unique
        ON schedule (pet_id, procedure_id, schedule_type_id, value)
        WHERE active = 1;
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS checklist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        pet_id INTEGER NOT NULL,
        procedure_id INTEGER NOT NULL,
        schedule_id INTEGER NOT NULL,
        status INTEGER NOT NULL CHECK (status IN (0, 1)) DEFAULT 0,
        active INTEGER NOT NULL CHECK (status IN (0, 1)) DEFAULT 0,

        FOREIGN KEY (pet_id) REFERENCES pet(id),
        FOREIGN KEY (procedure_id) REFERENCES procedure(id),
        FOREIGN KEY (schedule_id) REFERENCES schedule(id),

        UNIQUE (date, pet_id, procedure_id, active)
    );
    """)


def _init_schedule_types(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM schedule_types")

    if cursor.fetchone()[0] > 0:
        logger.info(
            "Таблица schedule_types уже заполнена",
            extra={"user": "system"}
        )
        return

    values = [
        "Каждые Х дней",
        "Каждую неделю",
        "Каждый месяц",
        "Каждый год",
        "Конкретный день"
    ]

    cursor.executemany(
        "INSERT INTO schedule_types (description) VALUES (?)",
        [(v,) for v in values]
    )

    logger.info(
        f"Таблица schedule_types инициализирована ({len(values)} записей)",
        extra={"user": "system"}
    )


def init_database(db_name: str = DB_NAME, user: str = USER_NAME) -> None:
    """
    Полная инициализация БД
    """
    is_new = not os.path.isfile(db_name)

    if is_new:
        logger.info(
            f"База данных '{db_name}' не найдена. Создание новой.",
            extra={"user": user}
        )
    else:
        logger.info(
            f"База данных '{db_name}' уже существует.",
            extra={"user": user}
        )

    with db_connection(db_name) as conn:
        _create_tables(conn)
        _init_schedule_types(conn)

    logger.info(
        "Инициализация базы данных завершена",
        extra={"user": user}
    )
