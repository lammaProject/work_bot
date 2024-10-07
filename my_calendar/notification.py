import asyncio
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo


class Notification:
    def __init__(self, application, db):
        self.db = db
        self.app = application

    async def send_notification(self, user_id, today_event, tomorrow_event, app):
        if today_event is None:
            today_message = "Сегодня завода нет 🌴"
        else:
            today_message = f"Сегодня завод: {'День☀️' if today_event else 'Ночь🌙'}"

        if tomorrow_event is None:
            tomorrow_message = "Завтра завода нет 🌴"
        else:
            tomorrow_message = (
                f"Завтра завод: {'День☀️' if tomorrow_event else 'Ночь🌙'}"
            )

        message = f"{today_message}\n{tomorrow_message}"
        await app.bot.send_message(chat_id=user_id, text=message)

    async def check_and_notify(self, app):
        now = datetime.now()
        tomorrow = now + timedelta(days=1)

        users = self.db.get_all_users()
        for user_id in users:
            today_date = now.strftime("%Y-%m-%d")
            tomorrow_date = tomorrow.strftime("%Y-%m-%d")

            today_event = self.db.get_event(user_id, today_date)
            tomorrow_event = self.db.get_event(user_id, tomorrow_date)

            await self.send_notification(user_id, today_event, tomorrow_event, app)

    async def notification_loop(self):
        moscow_tz = ZoneInfo("Europe/Moscow")
        notification_time = time(hour=23, minute=39)

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
                await self.check_and_notify(self.app)
            except Exception as e:
                print(f"Ошибка при отправке уведомлений: {e}")

    @classmethod
    def setup(cls, application, db):
        notification_instance = cls(application, db)
        return notification_instance.notification_loop()
