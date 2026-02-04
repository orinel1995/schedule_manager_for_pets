import asyncio
from datetime import datetime

from aiogram import Bot

from data_access.notification import Notification
from data_access.checklist import Checklist
from data_access.schedule import Schedule


async def notification_scheduler(bot: Bot):
    """
    Асинхронный планировщик ежедневных уведомлений.
    Проверяет время раз в минуту.
    """
    last_sent: dict[tuple[int, str], str] = {}

    while True:
        now = datetime.now().strftime("%H:%M")

        notification_repo = Notification()
        notifications = notification_repo.get_all_active()

        for item in notifications:
            user_id = int(item["user_id"])
            notify_time = item["value"]

            if notify_time != now:
                continue

            key = (user_id, now)
            today = datetime.now().date().isoformat()

            # защита от повторной отправки в ту же минуту
            if last_sent.get(key) == today:
                continue

            checklist_repo = Checklist(user=str(user_id))
            schedule_repo = Schedule(user=str(user_id))

            # Сначала формируем задачи на сегодня (аналогично /today_tasks),
            # чтобы расчёт процента не брал предыдущий день.
            today_schedules = schedule_repo.get_today()
            if today_schedules:
                checklist_repo.ensure_today_tasks(today_schedules)

            completion_rate = checklist_repo.get_today_completion()

            if completion_rate < 1.0:
                text = (
                    f"На сегодня выполнено {completion_rate:.0%} заданий!"
                )
            else:
                text = "Все задания выполнены, ты молодец! 🎉"

            try:
                await bot.send_message(user_id, text)
                last_sent[key] = today
            except Exception:
                # пользователь мог заблокировать бота — молча игнорируем
                pass

        await asyncio.sleep(60)
