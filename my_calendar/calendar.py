import asyncio
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

import calendar
from database.database import Database

db = Database()


def create_calendar(user_id, year, month):
    now = datetime.now()
    today = now.day

    markup = [
        [
            InlineKeyboardButton(
                f"{calendar.month_name[month]} {year}", callback_data="ignore"
            )
        ]
    ]

    week_days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    markup.append(
        [InlineKeyboardButton(day, callback_data="ignore") for day in week_days]
    )

    # Obtener eventos del mes
    events = db.get_events(user_id, year, month)
    event_dict = {
        datetime.strptime(date, "%Y-%m-%d").day: is_day for date, is_day in events
    }

    # Rastrear eventos nocturnos consecutivos
    consecutive_night_events = 0
    start_night_streak = 0

    row = []
    for day in range(1, calendar.monthrange(year, month)[1] + 1):
        display_day = str(day)
        if day == today and now.month == month and now.year == year:
            display_day = f"{display_day}🧐"

        date = f"{year}-{month:02d}-{day:02d}"
        event = db.get_event(user_id, date)
        if event is not None:
            if not event:
                consecutive_night_events += 1
                if consecutive_night_events == 2:
                    start_night_streak = day
            else:
                consecutive_night_events = 0
            display_day += "☀️" if event else "🌙"
        else:
            if (
                consecutive_night_events >= 2
                and start_night_streak <= day <= start_night_streak + 4
            ):
                display_day = f"😴{display_day}"
            else:
                consecutive_night_events = 0
                start_night_streak = 0

        row.append(
            InlineKeyboardButton(display_day, callback_data=f"day_{year}_{month}_{day}")
        )
        if len(row) == 7:
            markup.append(row)
            row = []

    if row:
        markup.append(row)

    markup.append(
        [
            InlineKeyboardButton("<<", callback_data=f"prev_{year}_{month}"),
            InlineKeyboardButton(">>", callback_data=f"next_{year}_{month}"),
        ]
    )

    return InlineKeyboardMarkup(markup)


def create_day_night_keyboard(user_id, year, month, day):
    date = f"{year}-{month:02d}-{day:02d}"
    event = db.get_event(user_id, date)

    keyboard = [
        [
            InlineKeyboardButton(
                "☀️ День", callback_data=f"add_day_{year}_{month}_{day}"
            ),
            InlineKeyboardButton(
                "🌙 Ночь", callback_data=f"add_night_{year}_{month}_{day}"
            ),
        ]
    ]

    # Добавляем кнопку "Удалить событие", если оно существует
    if event is not None:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "❌ Удалить событие",
                    callback_data=f"delete_event_{year}_{month}_{day}",
                )
            ]
        )

    keyboard.append(
        [InlineKeyboardButton("Отмена", callback_data=f"cancel_{year}_{month}")]
    )
    return InlineKeyboardMarkup(keyboard)


async def calendar_command(update: Update, context):
    now = datetime.now()
    user_id = update.effective_user.id
    await update.message.reply_text(
        "Выберите дату:", reply_markup=create_calendar(user_id, now.year, now.month)
    )


async def calendar_callback(update: Update, context):
    query = update.callback_query
    user_id = query.from_user.id
    # Если выбрана конкретная дата
    if query.data.startswith("day"):
        _, year, month, day = query.data.split("_")
        year, month, day = int(year), int(month), int(day)
        await query.edit_message_text(
            "Выберите тип события:",
            reply_markup=create_day_night_keyboard(user_id, year, month, day),
        )
        return

        # Если добавляется дневное или ночное событие
    if query.data.startswith("add_day") or query.data.startswith("add_night"):
        _, is_day, year, month, day = query.data.split("_")
        year, month, day = int(year), int(month), int(day)
        date = f"{year}-{month:02d}-{day:02d}"
        db.add_event(user_id, date, is_day == "day")
        event_type = "Дневное" if is_day == "day" else "Ночное"
        await query.edit_message_text(
            f"{event_type} событие добавлено на {day}.{month}.{year}"
        )
        await asyncio.sleep(1)
        await query.edit_message_text(
            f"{event_type} событие добавлено на {day}.{month}.{year}",
            reply_markup=create_calendar(user_id, year, month),
        )

        # Если удаляется событие
    if query.data.startswith("delete_event"):
        parts = query.data.split("_")
        if len(parts) == 5:
            _, year, month, day = parts[1:]
            year, month, day = int(year), int(month), int(day)
            date = f"{year}-{month:02d}-{day:02d}"
            event = db.get_event(user_id, date)
            if event is not None:
                db.delete_event(user_id, date)
                await query.edit_message_text(
                    f"Событие на {day}.{month}.{year} удалено."
                )
            else:
                await query.edit_message_text(
                    f"Событие на {day}.{month}.{year} не найдено."
                )
            await asyncio.sleep(1)
            await query.edit_message_text(
                "Выберите дату:", reply_markup=create_calendar(user_id, year, month)
            )
        else:
            await query.answer("Неверный формат данных.")

    elif query.data.startswith("prev") or query.data.startswith("next"):
        _, year, month = query.data.split("_")
        year, month = int(year), int(month)
        if query.data.startswith("prev"):
            month -= 1
            if month < 1:
                month = 12
                year -= 1
        else:  # next
            month += 1
            if month > 12:
                month = 1
                year += 1
        # Обработка отмены
    elif query.data.startswith("cancel"):
        _, year, month = query.data.split("_")
        year, month = int(year), int(month)
    else:
        # Если это неизвестный тип данных, игнорируем
        await query.answer()
        return

    # Обновляем календарь
    await query.edit_message_text(
        "Выберите дату:", reply_markup=create_calendar(user_id, year, month)
    )
