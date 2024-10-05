import asyncio
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from database.database import Database

db = Database()


async def send_notification(user_id, today_event, tomorrow_event, app):
    if today_event is None:
        today_message = "Выходной 🌴"
    else:
        today_message = (
            f"Сегодня у вас событие: {'День' if today_event else 'Ночь'} ☀️🌙"
        )

    if tomorrow_event is None:
        tomorrow_message = "Завтра выходной 🌴"
    else:
        tomorrow_message = (
            f"Завтра у вас событие: {'День' if tomorrow_event else 'Ночь'} ☀️🌙"
        )

    message = f"{today_message}\n{tomorrow_message}"
    await app.bot.send_message(chat_id=user_id, text=message)


async def check_and_notify(app):
    now = datetime.now()
    tomorrow = now + timedelta(days=1)

    users = db.get_all_users()
    for user_id in users:
        today_date = now.strftime("%Y-%m-%d")
        tomorrow_date = tomorrow.strftime("%Y-%m-%d")

        today_event = db.get_event(user_id, today_date)
        tomorrow_event = db.get_event(user_id, tomorrow_date)

        await send_notification(user_id, today_event, tomorrow_event, app)


async def notification_loop(app):
    moscow_tz = ZoneInfo("Europe/Moscow")
    notification_time = time(
        hour=21, minute=42
    )  # Время отправки уведомлений (23:40 по московскому времени)

    while True:
        now = datetime.now(moscow_tz)
        next_notification = datetime.combine(
            now.date(), notification_time, tzinfo=moscow_tz
        )

        if now > next_notification:
            next_notification += timedelta(days=1)

        delay = (next_notification - now).total_seconds()
        await asyncio.sleep(delay)

        try:
            await check_and_notify(app)
        except Exception as e:
            print(f"Ошибка при отправке уведомлений: {e}")
