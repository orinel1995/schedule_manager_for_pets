from aiogram.fsm.state import StatesGroup, State


class MenuStates(StatesGroup):
    action_select = State()
    update_time_waiting_input = State()
