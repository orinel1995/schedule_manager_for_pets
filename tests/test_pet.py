import sqlite3
import pytest
from datetime import date

from data_access.pet import Pet


@pytest.fixture
def temp_db(tmp_path):
    """
    Создаёт временную SQLite БД с таблицей pet.
    """
    db_path = tmp_path / "test.db"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE pet (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT,
            active INTEGER NOT NULL CHECK (active IN (0, 1))
        );
    """)

    conn.commit()
    conn.close()

    return str(db_path)


@pytest.fixture
def pet_repo(temp_db):
    """
    Репозиторий Pet, работающий с временной БД.
    """
    return Pet(db_name=temp_db, user="test_user")


def test_create_pet_success(pet_repo):
    pet_id = pet_repo.create(
        name="Барсик",
        pet_type="кот",
        start_date="2025-03-01"
    )

    assert pet_id == 1

    pet = pet_repo.get_by_id(pet_id)

    assert pet["name"] == "Барсик"
    assert pet["type"] == "кот"
    assert pet["start_date"] == "2025-03-01"
    assert pet["end_date"] is None
    assert pet["active"] is True


def test_create_pet_default_start_date(pet_repo):
    pet_id = pet_repo.create(name="Шарик", pet_type="пёс")

    pet = pet_repo.get_by_id(pet_id)

    assert pet["start_date"] == date.today().isoformat()


def test_create_duplicate_name_returns_existing_id(pet_repo):
    first_id = pet_repo.create(name="Рыжик", pet_type="кот")
    second_id = pet_repo.create(name="Рыжик", pet_type="кот")

    assert first_id == second_id

    pets = pet_repo.get_active()
    assert len(pets) == 1


def test_update_active_true_to_false_sets_end_date(pet_repo):
    pet_id = pet_repo.create(name="Белка", pet_type="кот")

    pet_repo.update_active(pet_id, False)

    pet = pet_repo.get_by_id(pet_id)

    assert pet["active"] is False
    assert pet["end_date"] == date.today().isoformat()


def test_update_active_false_to_true_clears_end_date(pet_repo):
    pet_id = pet_repo.create(name="Снежок", pet_type="кот")

    pet_repo.update_active(pet_id, False)
    pet_repo.update_active(pet_id, True)

    pet = pet_repo.get_by_id(pet_id)

    assert pet["active"] is True
    assert pet["end_date"] is None


def test_update_active_idempotent_true(pet_repo):
    pet_id = pet_repo.create(name="Идем", pet_type="кот")

    pet_repo.update_active(pet_id, True)

    pet = pet_repo.get_by_id(pet_id)

    assert pet["active"] is True
    assert pet["end_date"] is None


def test_update_name(pet_repo):
    pet_id = pet_repo.create(name="Кузя", pet_type="кот")

    pet_repo.update_name(pet_id, "Кузьма")

    pet = pet_repo.get_by_id(pet_id)
    assert pet["name"] == "Кузьма"


def test_update_type(pet_repo):
    pet_id = pet_repo.create(name="Лаки", pet_type="пёс")

    pet_repo.update_type(pet_id, "собака")

    pet = pet_repo.get_by_id(pet_id)
    assert pet["type"] == "собака"


def test_update_start_date_with_different_format(pet_repo):
    pet_id = pet_repo.create(name="Мурка", pet_type="кот")

    pet_repo.update_start_date(pet_id, "15.05.2025")

    pet = pet_repo.get_by_id(pet_id)
    assert pet["start_date"] == "2025-05-15"


def test_get_active_returns_only_active_pets(pet_repo):
    id1 = pet_repo.create(name="Альфа", pet_type="кот")
    id2 = pet_repo.create(name="Бета", pet_type="кот")

    pet_repo.update_active(id2, False)

    active_pets = pet_repo.get_active()

    assert len(active_pets) == 1
    assert active_pets[0]["id"] == id1


def test_delete_pet(pet_repo):
    pet_id = pet_repo.create(name="Удаляемый", pet_type="кот")

    pet_repo.delete(pet_id)

    pet = pet_repo.get_by_id(pet_id)
    assert pet is None
