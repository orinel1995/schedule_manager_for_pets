from aiogram.fsm.state import State, StatesGroup


class SchedulesStates(StatesGroup):
    # Главное меню расписаний
    action_select = State()
    waiting_for_pet_id = State()
    waiting_for_procedure_id = State()
    waiting_for_schedule_id = State()
    edit_select = State()
    waiting_for_schedule_type = State()
    waiting_for_schedule_value = State()
    deactivate_confirm = State()
    waiting_for_start_date = State()
    waiting_for_end_date = State()
