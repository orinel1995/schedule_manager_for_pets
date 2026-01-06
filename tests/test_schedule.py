import sqlite3
import pytest
from datetime import date, timedelta

from core.db import db_connection
from data_access.schedule import Schedule


# -------------------- FIXTURES --------------------

@pytest.fixture
def prepared_db(tmp_path):
    """
    Создаёт файловую SQLite БД с нужными таблицами и базовыми данными.
    """
    db_path = tmp_path / "test_schedule.db"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.executescript("""
        PRAGMA foreign_keys = ON;

        CREATE TABLE pet (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            active INTEGER NOT NULL
        );

        CREATE TABLE procedure (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            active INTEGER NOT NULL
        );

        CREATE TABLE schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER NOT NULL,
            procedure_id INTEGER NOT NULL,
            schedule_type_id INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            value TEXT NOT NULL,
            active INTEGER NOT NULL,

            FOREIGN KEY (pet_id) REFERENCES pet(id),
            FOREIGN KEY (procedure_id) REFERENCES procedure(id)
        );
    """)

    cursor.execute(
        "INSERT INTO pet (name, active) VALUES ('Барсик', 1)"
    )
    cursor.execute(
        "INSERT INTO procedure (name, description, active) "
        "VALUES ('Вакцинация', 'Плановая прививка', 1)"
    )

    conn.commit()
    conn.close()

    return str(db_path)


@pytest.fixture
def schedule(prepared_db):
    return Schedule(db_name=prepared_db, user="test_user")


# -------------------- TESTS --------------------

def test_every_day(schedule, prepared_db):
    today = date.today().isoformat()

    with db_connection(prepared_db) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO schedule
            (pet_id, procedure_id, schedule_type_id, start_date, value, active)
            VALUES (1, 1, 1, ?, '1', 1)
        """, (today,))

    result = schedule.get_today()

    assert len(result) == 1
    assert result[0]["pet_name"] == "Барсик"
    assert result[0]["procedure_name"] == "Вакцинация"


def test_every_x_days_not_today(schedule, prepared_db):
    start_date = (date.today() - timedelta(days=1)).isoformat()

    with db_connection(prepared_db) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO schedule
            (pet_id, procedure_id, schedule_type_id, start_date, value, active)
            VALUES (1, 1, 1, ?, '2', 1)
        """, (start_date,))

    result = schedule.get_today()
    assert result == []


def test_weekly_today(schedule, prepared_db):
    today = date.today()
    weekday_name = today.strftime("%A").upper()

    with db_connection(prepared_db) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO schedule
            (pet_id, procedure_id, schedule_type_id, start_date, value, active)
            VALUES (1, 1, 2, ?, ?, 1)
        """, (today.isoformat(), weekday_name))

    result = schedule.get_today()
    assert len(result) == 1


def test_weekly_not_today(schedule, prepared_db):
    today = date.today()
    wrong_day = (today + timedelta(days=1)).strftime("%A").upper()

    with db_connection(prepared_db) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO schedule
            (pet_id, procedure_id, schedule_type_id, start_date, value, active)
            VALUES (1, 1, 2, ?, ?, 1)
        """, (today.isoformat(), wrong_day))

    result = schedule.get_today()
    assert result == []


def test_monthly_today(schedule, prepared_db):
    today = date.today()
    day_value = str(today.day)

    with db_connection(prepared_db) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO schedule
            (pet_id, procedure_id, schedule_type_id, start_date, value, active)
            VALUES (1, 1, 3, ?, ?, 1)
        """, (today.isoformat(), day_value))

    result = schedule.get_today()
    assert len(result) == 1


def test_monthly_31_on_short_month(schedule, prepared_db):
    today = date(2024, 2, 29)
    start_date = today.isoformat()

    with db_connection(prepared_db) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO schedule
            (pet_id, procedure_id, schedule_type_id, start_date, value, active)
            VALUES (1, 1, 3, ?, '31', 1)
        """, (start_date,))

    result = schedule.get_today(today)
    assert len(result) == 1


def test_monthly_31_on_long_month(schedule, prepared_db):
    today = date(2025, 3, 28)  # март, 31 день

    with db_connection(prepared_db) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO schedule
            (pet_id, procedure_id, schedule_type_id, start_date, value, active)
            VALUES (1, 1, 3, ?, '31', 1)
        """, (today.isoformat(),))

    result = schedule.get_today(today)

    assert result == []


def test_yearly_today(schedule, prepared_db):
    today = date.today()
    value = today.strftime("%m-%d")

    with db_connection(prepared_db) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO schedule
            (pet_id, procedure_id, schedule_type_id, start_date, value, active)
            VALUES (1, 1, 4, ?, ?, 1)
        """, (today.isoformat(), value))

    result = schedule.get_today()
    assert len(result) == 1


def test_inactive_schedule_ignored(schedule, prepared_db):
    today = date.today().isoformat()

    with db_connection(prepared_db) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO schedule
            (pet_id, procedure_id, schedule_type_id, start_date, value, active)
            VALUES (1, 1, 1, ?, '1', 0)
        """, (today,))

    result = schedule.get_today()
    assert result == []


def test_inactive_pet_ignored(schedule, prepared_db):
    today = date.today().isoformat()

    with db_connection(prepared_db) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE pet SET active = 0 WHERE id = 1")
        cursor.execute("""
            INSERT INTO schedule
            (pet_id, procedure_id, schedule_type_id, start_date, value, active)
            VALUES (1, 1, 1, ?, '1', 1)
        """, (today,))

    result = schedule.get_today()
    assert result == []
