import os
import sqlite3

from core.logger import get_logger


logger = get_logger()

logger.info("Приложение запущено", extra={"user": "system"})


def create_database(db_name: str = "project.db") -> None:
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()

    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pet (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT,
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
        value TEXT NOT NULL,
        active INTEGER NOT NULL CHECK (active IN (0, 1)),
        parent_schedule INTEGER DEFAULT NULL,

        FOREIGN KEY (pet_id) REFERENCES pet(id) ON DELETE CASCADE,
        FOREIGN KEY (procedure_id) REFERENCES procedure(id) ON DELETE CASCADE,
        FOREIGN KEY (schedule_type_id) REFERENCES schedule_types(id) ON DELETE CASCADE,
        FOREIGN KEY (parent_schedule) REFERENCES schedule(id) ON DELETE SET NULL
    );
    """)

    # уникальный индекс только для активных записей
    cursor.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS uq_schedule_active_unique
        ON schedule (pet_id, procedure_id, schedule_type_id, value)
        WHERE active = 1;
    """)

    connection.commit()
    connection.close()


def init_schedule_types(connection: sqlite3.Connection) -> None:
    """
    Инициализирует справочник schedule_types фиксированными значениями,
    если таблица пуста.
    """
    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM schedule_types")
    count = cursor.fetchone()[0]

    if count > 0:
        logger.info(
            "Таблица schedule_types уже заполнена",
            extra={"user": "system"}
        )
        return

    schedule_types = [
        "Каждые Х дней",
        "Каждую неделю",
        "Каждый месяц",
        "Каждый год",
        "Конкретный день"
    ]

    cursor.executemany(
        "INSERT INTO schedule_types (description) VALUES (?)",
        [(value,) for value in schedule_types]
    )

    connection.commit()

    logger.info(
        f"Таблица schedule_types инициализирована ({len(schedule_types)} записей)",
        extra={"user": "system"}
    )


def init_database(db_name: str = "project.db", user: str = "admin") -> None:
    """
    Проверяет наличие базы данных, создаёт таблицы и инициализирует справочники.
    Логирует результат в CSV-файл.
    """
    is_new_db = not os.path.isfile(db_name)

    if is_new_db:
        logger.info(
            f"База данных '{db_name}' не найдена. Создание новой базы.",
            extra={"user": user}
        )
        create_database(db_name)
        logger.info(
            f"База данных '{db_name}' успешно создана.",
            extra={"user": user}
        )
    else:
        logger.info(
            f"База данных '{db_name}' уже существует.",
            extra={"user": user}
        )

    connection = sqlite3.connect(db_name)
    try:
        init_schedule_types(connection)
    finally:
        connection.close()


if __name__ == "__main__":
    init_database()
