import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

# handlers
from handlers.menu import router as menu_router
from handlers.pets import router as pets_router


def create_bot_and_dispatcher() -> tuple[Bot, Dispatcher]:
    """
    Создаёт и настраивает Bot и Dispatcher.
    НЕ запускает polling.
    """
    load_dotenv()

    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("Переменная окружения BOT_TOKEN не задана")

    bot = Bot(token=token)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(menu_router)
    dp.include_router(pets_router)

    return bot, dp
