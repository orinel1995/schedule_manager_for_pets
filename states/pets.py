from aiogram.fsm.state import StatesGroup, State


class PetsStates(StatesGroup):
    """
    FSM-состояния для управления питомцами.
    """
    create_waiting_input = State()
    select_waiting_id = State()
    action_select = State()
    rename_waiting = State()
    type_waiting = State()
    date_waiting = State()
    deactivate_confirm = State()
