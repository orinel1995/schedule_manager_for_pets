import asyncio

from core.db import init_database
from core.logger import get_logger
from bot import create_bot_and_dispatcher


logger = get_logger()


async def main() -> None:
    """
    Точка входа приложения.
    """
    init_database()
    bot, dp = create_bot_and_dispatcher()

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
