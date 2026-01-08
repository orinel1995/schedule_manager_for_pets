from aiogram.fsm.state import State, StatesGroup


class SchedulesStates(StatesGroup):
    # Главное меню расписаний
    action_select = State()

    # ---------- СОЗДАНИЕ ----------
    waiting_for_pet_id = State()
    waiting_for_procedure_id = State()

    # ---------- ВЫБОР СУЩЕСТВУЮЩЕГО ----------
    waiting_for_schedule_id = State()

    # ---------- ДЕЙСТВИЯ С РАСПИСАНИЕМ ----------
    edit_select = State()

    # ---------- РЕДАКТИРОВАНИЕ ПЕРИОДИЧНОСТИ ----------
    waiting_for_schedule_type = State()
    waiting_for_schedule_value = State()

    # ---------- ДЕАКТИВАЦИЯ ----------
    deactivate_confirm = State()
