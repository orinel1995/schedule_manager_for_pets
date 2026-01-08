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

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
