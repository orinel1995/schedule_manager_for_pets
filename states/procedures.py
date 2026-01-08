from aiogram.fsm.state import State, StatesGroup


class ProcedureStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_id = State()
    waiting_for_description = State()
    waiting_for_deactivate_id = State()
    action_select = State()
    deactivate_confirm = State()
