import asyncio
import logging
import os

from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
)

from database.database import Database
from my_calendar.notification import Notification
from my_calendar.telegram_calendar import Calendar

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

db = Database()


# В начале файла добавьте:
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def error_handler(update: Update, context):
    logger.error(f"Exception while handling an update: {context.error}")


async def start(update: Update, context):
    keyboard = [["Календарь"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Скоро на завод", reply_markup=reply_markup)


async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    Calendar.setup(application=app, db=db)

    app.add_error_handler(error_handler)

    try:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(poll_interval=1)

        await asyncio.create_task(Notification.setup(application=app, db=db))

        await asyncio.Event().wait()  # Ожидание завершения работы бота
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
