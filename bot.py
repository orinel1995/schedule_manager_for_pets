import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

# handlers
from handlers.menu import router as menu_router
from handlers.pets import router as pets_router


async def main() -> None:
    # --- Загрузка переменных окружения ---
    load_dotenv()

    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("Переменная окружения BOT_TOKEN не задана")

    # --- Логирование ---
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    # --- Инициализация бота ---
    bot = Bot(token=token)
    dp = Dispatcher(storage=MemoryStorage())

    # --- Регистрация роутеров ---
    dp.include_router(menu_router)
    dp.include_router(pets_router)

    # --- Запуск ---
    logging.info("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
