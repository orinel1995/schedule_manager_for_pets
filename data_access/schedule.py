"""
Модуль доступа к данным таблицы schedule.

Отвечает за создание, изменение, активацию и получение расписаний процедур
для питомцев.

Модуль хранит только декларативные правила расписаний,
фактический расчёт дат выполнения выносится в отдельную логику.
"""

from datetime import date
from enum import Enum
from typing import List, Dict, Optional, Union, Iterable

from core.logger import get_logger
from core.db import db_connection
from core.dates import (
    parse_user_date,
    normalize_yearly_date,
    last_day_of_month,
)

logger = get_logger()


# -------------------- ENUM ДНЕЙ НЕДЕЛИ --------------------

class WeekDay(Enum):
    MONDAY = ("пн", "понедельник")
    TUESDAY = ("вт", "вторник")
    WEDNESDAY = ("ср", "среда")
    THURSDAY = ("чт", "четверг")
    FRIDAY = ("пт", "пятница")
    SATURDAY = ("сб", "суббота")
    SUNDAY = ("вс", "воскресенье")

    @classmethod
    def parse(cls, value: str) -> "WeekDay":
        normalized = value.strip().lower()

        for day in cls:
            if normalized in day.value:
                return day

        raise ValueError(f"Неизвестный день недели: {value}")

    @classmethod
    def parse_many(cls, value: str) -> List["WeekDay"]:
        return [cls.parse(part) for part in value.split(",")]


# -------------------- ОСНОВНОЙ КЛАСС --------------------

class Schedule:
    """
    Класс для работы с пользовательскими расписаниями процедур.
    """

    def __init__(self, db_name: str = "project.db", user: str = "admin"):
        self.db_name = db_name
        self.user = user

    # ---------- СОЗДАНИЕ ----------

    def create(
        self,
        pet_id: int,
        procedure_id: int,
        start_date: Optional[str] = None
    ) -> int:
        """
        Создаёт расписание по умолчанию:
        - Каждые 1 день
        """
        start_date = parse_user_date(start_date) or date.today().isoformat()

        with db_connection(self.db_name) as conn:
            cursor = conn.cursor()

            # --- НОВОЕ: проверка на существующее расписание ---
            cursor.execute(
                """
                SELECT id
                FROM schedule
                WHERE pet_id = ?
                AND procedure_id = ?
                AND schedule_type_id = 1
                AND active = 1
                """,
                (pet_id, procedure_id),
            )

            row = cursor.fetchone()
            if row:
                logger.info(
                    f"Найдено расписание id={row[0]} (pet_id={pet_id}, procedure_id={procedure_id})",
                    extra={"user": self.user}
                )
                return row[0]

            # --- Старое поведение без изменений ---
            cursor.execute(
                """
                INSERT INTO schedule (
                    pet_id,
                    procedure_id,
                    schedule_type_id,
                    start_date,
                    value,
                    active
                )
                VALUES (?, ?, 1, ?, '1', 1)
                """,
                (pet_id, procedure_id, start_date),
            )

            schedule_id = cursor.lastrowid

        logger.info(
            f"Создано расписание id={schedule_id} (pet_id={pet_id}, procedure_id={procedure_id})",
            extra={"user": self.user}
        )

        return schedule_id

    # ---------- ИЗМЕНЕНИЕ РАСПИСАНИЯ ----------

    def update_schedule(
        self,
        schedule_id: int,
        schedule_type_id: int,
        input_value: str
    ) -> None:
        """
        Обновляет расписание:
        - Если исходная запись активна, она деактивируется.
        - Создаётся новая запись с заданным типом и значением.
        - Для weekly, monthly, yearly, current_day создаются дочерние записи по правилам.
        """
        with db_connection(self.db_name) as conn:
            cursor = conn.cursor()

            # Берём исходное расписание
            cursor.execute("""
                SELECT *
                FROM schedule
                WHERE id = ? AND active = 1
            """, (schedule_id,))
            base = cursor.fetchone()

            if base is None:
                logger.error(
                    f"Расписание id={schedule_id} неактивно или не найдено, обновление пропущено",
                    extra={"user": self.user}
                )
                return

            # Деактивируем исходную запись
            cursor.execute("UPDATE schedule SET active = 0 WHERE id = ?", (schedule_id,))

            # Базовая структура для нового расписания
            new_base = {
                "pet_id": base["pet_id"],
                "procedure_id": base["procedure_id"],
                "start_date": base["start_date"],
            }

            # --- WEEKLY: создаём дочерние записи на дни недели ---
            if schedule_type_id == 2:
                self._create_weekly(cursor, new_base, input_value, parent_id=schedule_id)

            # --- MONTHLY ---
            elif schedule_type_id == 3:
                self._create_monthly(cursor, new_base, input_value, parent_id=schedule_id)

            # --- YEARLY ---
            elif schedule_type_id == 4:
                self._create_yearly(cursor, new_base, input_value, parent_id=schedule_id)

            # --- CURRENT DAY / Конкретный день ---
            elif schedule_type_id == 5:
                self._create_current_day(cursor, new_base, input_value, parent_id=schedule_id)

            # --- DAILY / Каждые X дней ---
            elif schedule_type_id == 1:
                self._create_each_x_days(cursor, new_base, input_value, parent_id=schedule_id)

            else:
                raise ValueError("Неизвестный schedule_type_id")

        logger.info(
            f"Расписание id={schedule_id} обновлено, создано новое дочернее расписание type={schedule_type_id}",
            extra={"user": self.user}
        )

    # ---------- ПОЛУЧЕНИЕ ----------

    def get_today(self, today: Optional[date] = None) -> List[Dict]:
        """
        Возвращает список процедур, которые должны быть выполнены сегодня.
        """
        if today is None:
            today = date.today()
        day_of_month = today.day
        month_day = today.strftime("%m-%d")
        today_iso = today.isoformat()

        result: List[Dict] = []

        with db_connection(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    s.schedule_type_id,
                    s.value,
                    s.start_date,
                    p.name AS pet_name,
                    pr.name AS procedure_name,
                    pr.description AS procedure_description
                FROM schedule s
                JOIN pet p ON p.id = s.pet_id
                JOIN procedure pr ON pr.id = s.procedure_id
                WHERE s.active = 1
                  AND p.active = 1
                  AND pr.active = 1
                  AND s.start_date <= ?
            """, (today_iso,))

            rows = cursor.fetchall()

        for row in rows:
            execute_today = False
            schedule_type = row["schedule_type_id"]
            value = row["value"]
            start_date = date.fromisoformat(row["start_date"])

            # 1. Каждые X дней
            if schedule_type == 1:
                delta_days = (today - start_date).days
                if delta_days % int(value) == 0:
                    execute_today = True

            # 2. Каждую неделю
            elif schedule_type == 2:
                try:
                    scheduled_weekday = value.upper()
                    today_weekday = today.strftime("%A").upper()
                    if scheduled_weekday == today_weekday:
                        execute_today = True
                except Exception:
                    logger.error(
                        f"Некорректный weekly value: {value}",
                        extra={"user": self.user}
                    )

            elif schedule_type == 3:
                target_day = int(value)
                last_day = last_day_of_month(today)

                if target_day >= last_day:
                    # 29–31 → всегда последний день месяца
                    if day_of_month == last_day:
                        execute_today = True
                else:
                    if day_of_month == target_day:
                        execute_today = True

            # 4. Каждый год
            elif schedule_type == 4:
                if month_day == value:
                    execute_today = True
                    
            # 5. Конкретный день
            elif schedule_type == 5:
                if value == today_iso:
                    execute_today = True

            if execute_today:
                result.append({
                    "pet_name": row["pet_name"],
                    "procedure_name": row["procedure_name"],
                    "procedure_description": row["procedure_description"],
                })


        logger.info(
            f"Получено процедур на сегодня: {len(result)}",
            extra={"user": self.user}
        )

        return result

    def get_active(self, pet_id: Optional[int] = None) -> List[Dict]:
        """
        Возвращает список всех активных расписаний.
        Если указан pet_id, возвращаются только расписания этого питомца.
        """
        result: List[Dict] = []

        with db_connection(self.db_name) as conn:
            cursor = conn.cursor()

            sql = """
                SELECT
                    s.id,
                    s.pet_id,
                    p.name AS pet_name,
                    s.procedure_id,
                    pr.name AS procedure_name,
                    s.schedule_type_id,
                    st.description AS schedule_type_description,
                    s.start_date,
                    s.value,
                    s.active
                FROM schedule s
                JOIN pet p ON p.id = s.pet_id
                JOIN procedure pr ON pr.id = s.procedure_id
                JOIN schedule_types st ON st.id = s.schedule_type_id
                WHERE s.active = 1
                AND p.active = 1
                AND pr.active = 1
            """

            params: List[Union[int, str]] = []
            if pet_id is not None:
                sql += " AND s.pet_id = ?"
                params.append(pet_id)

            sql += " ORDER BY s.id"

            cursor.execute(sql, params)

            columns = [col[0] for col in cursor.description]
            for row in cursor.fetchall():
                result.append(dict(zip(columns, row)))

        return result

    # ---------- АКТИВАЦИЯ / УДАЛЕНИЕ ----------

    def set_active(
        self,
        schedule_ids: Union[int, Iterable[int]],
        active: bool
    ) -> None:
        if isinstance(schedule_ids, int):
            ids = [schedule_ids]
        else:
            ids = list(schedule_ids)

        if not ids:
            return

        placeholders = ",".join("?" for _ in ids)

        with db_connection(self.db_name) as conn:
            conn.execute(
                f"""
                UPDATE schedule
                SET active = ?
                WHERE id IN ({placeholders})
                OR parent_schedule IN ({placeholders})
                """,
                [int(active)] + ids + ids
            )

        logger.info(
            f"Обновлено active={active} для расписаний ids={ids}",
            extra={"user": self.user}
        )

    def delete(self, schedule_id: int) -> None:
        with db_connection(self.db_name) as conn:
            conn.execute("DELETE FROM schedule WHERE id = ?", (schedule_id,))

        logger.info(
            f"Расписание id={schedule_id} удалено",
            extra={"user": self.user}
        )

    # -------------------- ВНУТРЕННИЕ МЕТОДЫ --------------------

    def _create_current_day(
        self,
        cursor,
        base,
        value: str,
        parent_id: int | None = None
    ) -> None:
        """
        Создаёт расписание на конкретный день.
        - value: дата в формате YYYY-MM-DD
        """
        try:
            # Приводим к ISO-формату и проверяем корректность
            day = parse_user_date(value)
            if day is None:
                raise ValueError("Некорректная дата для одноразового расписания")

            cursor.execute("""
                INSERT INTO schedule (
                    pet_id,
                    procedure_id,
                    schedule_type_id,
                    start_date,
                    value,
                    active,
                    parent_schedule
                )
                VALUES (?, ?, 5, ?, ?, 1, ?)
            """, (
                base["pet_id"],
                base["procedure_id"],
                base["start_date"],
                day,
                parent_id
            ))
        except Exception:
            logger.error(
                f"Не удалось добавить одноразовое расписание: pet_id={base['pet_id']}, "
                f"procedure_id={base['procedure_id']}, value={value}, parent_id={parent_id}",
                extra={"user": self.user}
            )

    def _create_each_x_days(self, cursor, base, value: str, parent_id: int | None = None) -> None:
        try:
            cursor.execute("""
                INSERT INTO schedule (
                    pet_id,
                    procedure_id,
                    schedule_type_id,
                    start_date,
                    value,
                    active,
                    parent_schedule
                )
                VALUES (?, ?, 1, ?, ?, 1, ?)
            """, (
                base["pet_id"],
                base["procedure_id"],
                base["start_date"],
                str(int(value)),
                parent_id
            ))
        except Exception:
            logger.error(
                f"Не удалось добавить ежедневное расписание: pet_id={base['pet_id']}, "
                f"procedure_id={base['procedure_id']}, value={value}, parent_id={parent_id}",
                extra={"user": self.user}
            )

    def _create_weekly(self, cursor, base, value: str, parent_id: int | None = None) -> None:
        days = WeekDay.parse_many(value)
        for day in days:
            try:
                cursor.execute("""
                    INSERT INTO schedule (
                        pet_id,
                        procedure_id,
                        schedule_type_id,
                        start_date,
                        value,
                        active,
                        parent_schedule
                    )
                    VALUES (?, ?, 2, ?, ?, 1, ?)
                """, (
                    base["pet_id"],
                    base["procedure_id"],
                    base["start_date"],
                    day.name,
                    parent_id
                ))
            except Exception:
                logger.error(
                    f"Не удалось добавить недельное расписание: pet_id={base['pet_id']}, "
                    f"procedure_id={base['procedure_id']}, day={day.name}, parent_id={parent_id}",
                    extra={"user": self.user}
                )

    def _create_monthly(self, cursor, base, value: str, parent_id: int | None = None) -> None:
        day = int(value)
        if not 1 <= day <= 31:
            raise ValueError("День месяца должен быть от 1 до 31")

        try:
            cursor.execute("""
                INSERT INTO schedule (
                    pet_id,
                    procedure_id,
                    schedule_type_id,
                    start_date,
                    value,
                    active,
                    parent_schedule
                )
                VALUES (?, ?, 3, ?, ?, 1, ?)
            """, (
                base["pet_id"],
                base["procedure_id"],
                base["start_date"],
                str(day),
                parent_id
            ))
        except Exception:
            logger.error(
                f"Не удалось добавить месячное расписание: pet_id={base['pet_id']}, "
                f"procedure_id={base['procedure_id']}, day={day}, parent_id={parent_id}",
                extra={"user": self.user}
            )

    def _create_yearly(self, cursor, base, value: str, parent_id: int | None = None) -> None:
        try:
            normalized = normalize_yearly_date(value)
            cursor.execute("""
                INSERT INTO schedule (
                    pet_id,
                    procedure_id,
                    schedule_type_id,
                    start_date,
                    value,
                    active,
                    parent_schedule
                )
                VALUES (?, ?, 4, ?, ?, 1, ?)
            """, (
                base["pet_id"],
                base["procedure_id"],
                base["start_date"],
                normalized,
                parent_id
            ))
        except ValueError:
            logger.error(
                f"Некорректный формат даты для ежегодного расписания: '{value}' "
                f"(pet_id={base['pet_id']}, procedure_id={base['procedure_id']}, parent_id={parent_id})",
                extra={"user": self.user}
            )
        except Exception:
            logger.error(
                f"Не удалось добавить ежегодное расписание: pet_id={base['pet_id']}, "
                f"procedure_id={base['procedure_id']}, value={value}, parent_id={parent_id}",
                extra={"user": self.user}
            )
