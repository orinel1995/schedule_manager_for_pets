import sqlite3
import pytest

from data_access.procedure import Procedure


@pytest.fixture
def temp_db(tmp_path):
    """
    Создаёт временную SQLite БД с таблицей procedure.
    """
    db_path = tmp_path / "test.db"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE procedure (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            active INTEGER NOT NULL CHECK (active IN (0, 1))
        );
    """)

    conn.commit()
    conn.close()

    return str(db_path)


@pytest.fixture
def procedure_repo(temp_db):
    """
    Репозиторий Procedure, работающий с временной БД.
    """
    return Procedure(db_name=temp_db, user="test_user")


def get_procedure_raw(db_name: str, procedure_id: int):
    """
    Вспомогательная функция для чтения записи напрямую из БД.
    """
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, description, active
        FROM procedure
        WHERE id = ?
    """, (procedure_id,))

    row = cursor.fetchone()
    conn.close()

    return row


def test_create_procedure_success(procedure_repo, temp_db):
    procedure_id = procedure_repo.create(
        name="Вакцинация",
        description="Ежегодная вакцинация"
    )

    assert procedure_id == 1

    row = get_procedure_raw(temp_db, procedure_id)

    assert row["name"] == "Вакцинация"
    assert row["description"] == "Ежегодная вакцинация"
    assert row["active"] == 1


def test_create_procedure_without_description(procedure_repo, temp_db):
    procedure_id = procedure_repo.create(name="Осмотр")

    row = get_procedure_raw(temp_db, procedure_id)

    assert row["name"] == "Осмотр"
    assert row["description"] is None
    assert row["active"] == 1


def test_create_duplicate_name_returns_existing_id(procedure_repo, temp_db):
    first_id = procedure_repo.create(
        name="Чистка зубов",
        description="Ультразвуковая"
    )
    second_id = procedure_repo.create(
        name="Чистка зубов",
        description="Другая"
    )

    assert first_id == second_id

    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM procedure")
    count = cursor.fetchone()[0]

    conn.close()

    assert count == 1


def test_update_active(procedure_repo, temp_db):
    procedure_id = procedure_repo.create(name="Стерилизация")

    procedure_repo.update_active(procedure_id, False)

    row = get_procedure_raw(temp_db, procedure_id)

    assert row["active"] == 0


def test_update_description(procedure_repo, temp_db):
    procedure_id = procedure_repo.create(
        name="Анализ крови",
        description="Общий"
    )

    procedure_repo.update_description(
        procedure_id,
        "Биохимический"
    )

    row = get_procedure_raw(temp_db, procedure_id)

    assert row["description"] == "Биохимический"


def test_delete_procedure(procedure_repo, temp_db):
    procedure_id = procedure_repo.create(name="Удаляемая")

    procedure_repo.delete(procedure_id)

    row = get_procedure_raw(temp_db, procedure_id)

    assert row is None


def test_get_procedure_by_id(procedure_repo):
    procedure_id = procedure_repo.create(
        name="Рентген",
        description="Снимок грудной клетки"
    )

    procedure = procedure_repo.get_by_id(procedure_id)

    assert procedure is not None
    assert procedure["id"] == procedure_id
    assert procedure["name"] == "Рентген"
    assert procedure["description"] == "Снимок грудной клетки"
    assert procedure["active"] is True


def test_get_active_procedures(procedure_repo):
    id1 = procedure_repo.create(name="Процедура 1")
    id2 = procedure_repo.create(name="Процедура 2")

    procedure_repo.update_active(id2, False)

    active = procedure_repo.get_active()

    assert len(active) == 1
    assert active[0]["id"] == id1
    assert active[0]["active"] is True
