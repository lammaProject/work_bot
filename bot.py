import asyncio
import logging
import os

from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    filters,
    MessageHandler,
)

from my_calendar.calendar import calendar_command, calendar_callback
from my_calendar.notification import notification_loop

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")


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
    app.add_handler(MessageHandler(filters.Text(["Календарь"]), calendar_command))
    app.add_handler(CallbackQueryHandler(calendar_callback))
    app.add_error_handler(error_handler)

    print("Бот запущен...")
    try:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(poll_interval=1)

        await asyncio.create_task(notification_loop(app))

        await asyncio.Event().wait()  # Ожидание завершения работы бота
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
