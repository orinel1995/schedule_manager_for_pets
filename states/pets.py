from aiogram.fsm.state import StatesGroup, State


class PetsStates(StatesGroup):
    """
    FSM-состояния для управления питомцами.
    """

    # --- Создание питомца ---
    create_waiting_input = State()

    # --- Выбор существующего питомца ---
    select_waiting_id = State()

    # --- Выбор действия над питомцем ---
    action_select = State()

    # --- Редактирование ---
    rename_waiting = State()
    type_waiting = State()
    date_waiting = State()

    # --- Деактивация ---
    deactivate_confirm = State()
