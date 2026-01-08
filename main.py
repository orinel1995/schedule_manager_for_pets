import asyncio

from core.db import init_database
from core.logger import get_logger
from bot import create_bot_and_dispatcher
from aiogram.types import BotCommand, MenuButtonCommands


logger = get_logger()


async def main() -> None:
    """
    Точка входа приложения.
    """
    init_database()
    bot, dp = create_bot_and_dispatcher()
    await bot.set_my_commands([
        BotCommand(command="pets", description="🐾 Питомцы"),
        BotCommand(command="procedures", description="🧪 Процедуры"),
        BotCommand(command="schedules", description="📅 Расписания"),
        BotCommand(command="today_tasks", description="📋 Задания на сегодня"),
    ])

    await bot.set_chat_menu_button(
        menu_button=MenuButtonCommands()
    )
    logger.info("Telegram-бот запущен", extra={"user": "system"})

    try:
        await dp.start_polling(bot)

    except asyncio.CancelledError:
        # Нормальная остановка (Ctrl+C, SIGTERM)
        logger.info("Telegram-бот остановлен", extra={"user": "system"})
        raise

    except Exception:
        # Любая реальная ошибка
        logger.exception(
            "Ошибка при работе Telegram-бота",
            extra={"user": "system"}
        )
        raise

    finally:
        logger.info("Завершение работы приложения", extra={"user": "system"})


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Ctrl+C на уровне asyncio.run
        logger.info("Приложение остановлено пользователем (Ctrl+C)", extra={"user": "system"})
